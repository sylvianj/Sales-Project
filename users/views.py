# users/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django_otp import devices_for_user
from django_otp.plugins.otp_totp.models import TOTPDevice
from .models import UserRole, User2FA, BlacklistedToken
from .serializers import LoginSerializer
import pyotp
import qrcode
import io
import base64
import json
import random


class AuthViewSet(viewsets.ViewSet):
    """Authentication endpoints (login, logout, refresh, 2FA)"""

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            return Response({'error': 'Account disabled'}, status=status.HTTP_401_UNAUTHORIZED)

        # Get roles
        user_roles = UserRole.objects.filter(user=user)
        roles = [ur.role.name for ur in user_roles]

        # Check 2FA
        try:
            twofa = User2FA.objects.get(user=user)
            requires_2fa = twofa.is_enabled
        except User2FA.DoesNotExist:
            requires_2fa = False

        if not requires_2fa:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'roles': roles
                }
            })

        # 2FA required – return temporary token
        temp_token = RefreshToken.for_user(user)
        temp_token['temp'] = True
        return Response({
            'requires_2fa': True,
            'temp_token': str(temp_token),
            'user_id': user.id,
            'username': user.username
        })

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def verify_2fa(self, request):
        temp_token = request.data.get('temp_token')
        code = request.data.get('code')
        backup_code = request.data.get('backup_code')

        if not temp_token:
            return Response({'error': 'Temp token required'}, status=400)

        try:
            access_token = AccessToken(temp_token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)
        except Exception:
            return Response({'error': 'Invalid temp token'}, status=401)

        verified = False
        if code:
            devices = devices_for_user(user)
            for device in devices:
                if device.verify_token(code):
                    verified = True
                    break
        if backup_code:
            try:
                twofa = User2FA.objects.get(user=user)
                backup_codes = json.loads(twofa.backup_codes or '[]')
                if backup_code in backup_codes:
                    backup_codes.remove(backup_code)
                    twofa.backup_codes = json.dumps(backup_codes)
                    twofa.save()
                    verified = True
            except User2FA.DoesNotExist:
                pass

        if not verified:
            return Response({'error': 'Invalid 2FA code'}, status=401)

        refresh = RefreshToken.for_user(user)
        roles = [ur.role.name for ur in UserRole.objects.filter(user=user)]
        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'roles': roles
            }
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            access_token = request.data.get('access_token')
            if access_token:
                BlacklistedToken.objects.create(token=access_token)
            return Response({'message': 'Logged out'}, status=200)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def refresh(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({'error': 'Refresh token required'}, status=400)
        try:
            refresh = RefreshToken(refresh_token)
            return Response({'access_token': str(refresh.access_token)})
        except Exception:
            return Response({'error': 'Invalid refresh token'}, status=401)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        roles = [ur.role.name for ur in UserRole.objects.filter(user=user)]
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'roles': roles
        })

    # 2FA management endpoints
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def setup_2fa(self, request):
        user = request.user
        secret = pyotp.random_base32()
        device, _ = TOTPDevice.objects.get_or_create(user=user, name='default')
        device.key = secret
        device.save()

        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=user.email, issuer_name="Sales System")
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        backup_codes = [str(random.randint(10000000, 99999999)) for _ in range(10)]

        twofa, _ = User2FA.objects.get_or_create(user=user)
        twofa.secret_key = secret
        twofa.backup_codes = json.dumps(backup_codes)
        twofa.save()

        return Response({
            'secret': secret,
            'qr_code': f"data:image/png;base64,{qr_base64}",
            'backup_codes': backup_codes
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def enable_2fa(self, request):
        code = request.data.get('code')
        user = request.user
        devices = devices_for_user(user)
        verified = any(d.verify_token(code) for d in devices)
        if not verified:
            return Response({'error': 'Invalid code'}, status=400)
        twofa, _ = User2FA.objects.get_or_create(user=user)
        twofa.is_enabled = True
        twofa.save()
        return Response({'message': '2FA enabled'})

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def disable_2fa(self, request):
        code = request.data.get('code')
        user = request.user
        devices = devices_for_user(user)
        verified = any(d.verify_token(code) for d in devices)
        if not verified:
            return Response({'error': 'Invalid code'}, status=400)
        twofa = User2FA.objects.get(user=user)
        twofa.is_enabled = False
        twofa.save()
        return Response({'message': '2FA disabled'})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def twofa_status(self, request):
        try:
            twofa = User2FA.objects.get(user=request.user)
            return Response({'enabled': twofa.is_enabled, 'has_backup_codes': bool(twofa.backup_codes)})
        except User2FA.DoesNotExist:
            return Response({'enabled': False, 'has_backup_codes': False})