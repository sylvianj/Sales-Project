# users/views.py
import json, io, base64, random
import pyotp, qrcode
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

class AuthViewSet(viewsets.ViewSet):
    """Authentication endpoints (login, logout, refresh, 2FA)"""

    def _get_user_data(self, user):
        """Serialize user with roles."""
        roles = [ur.role.name for ur in UserRole.objects.filter(user=user)]
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'roles': roles,
            'role': roles[0] if roles else ('admin' if user.is_superuser else 'cashier'),
            'is_active': user.is_active,
        }

    def _verify_2fa(self, user, code=None, backup_code=None):
        """Verify 2FA code or backup code."""
        if code:
            return any(d.verify_token(code) for d in devices_for_user(user))
        
        if backup_code:
            try:
                twofa = User2FA.objects.get(user=user)
                backup_codes = json.loads(twofa.backup_codes or '[]')
                if backup_code in backup_codes:
                    backup_codes.remove(backup_code)
                    twofa.backup_codes = json.dumps(backup_codes)
                    twofa.save()
                    return True
            except User2FA.DoesNotExist:
                pass
        return False

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Username and password required'}, status=400)

        user = authenticate(username=username, password=password)
        if not user or not user.is_active:
            return Response({'error': 'Invalid credentials' if not user else 'Account disabled'}, status=401)

        # Check 2FA requirement
        try:
            requires_2fa = User2FA.objects.get(user=user).is_enabled
        except User2FA.DoesNotExist:
            requires_2fa = False

        if not requires_2fa:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': self._get_user_data(user)
            })

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
        if not temp_token:
            return Response({'error': 'Temp token required'}, status=400)

        try:
            user_id = AccessToken(temp_token)['user_id']
            user = User.objects.get(id=user_id)
        except Exception:
            return Response({'error': 'Invalid temp token'}, status=401)

        if not self._verify_2fa(user, request.data.get('code'), request.data.get('backup_code')):
            return Response({'error': 'Invalid 2FA code'}, status=401)

        refresh = RefreshToken.for_user(user)
        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': self._get_user_data(user)
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        try:
            if refresh_token := request.data.get('refresh_token'):
                RefreshToken(refresh_token).blacklist()
            if access_token := request.data.get('access_token'):
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
            return Response({'access_token': str(RefreshToken(refresh_token).access_token)})
        except Exception:
            return Response({'error': 'Invalid refresh token'}, status=401)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        return Response(self._get_user_data(request.user))

    def list(self, request):
        """GET /api/users/  -> list all users (for the Users management page)."""
        return Response([self._get_user_data(u) for u in User.objects.all().order_by('username')])

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """POST /api/users/register/ -> create a user and assign a role."""
        data = request.data
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return Response({'message': 'Username and password are required'}, status=400)
        if User.objects.filter(username=username).exists():
            return Response({'message': 'Username already taken', 'username': ['Already taken']}, status=400)

        user = User.objects.create_user(
            username=username,
            password=password,
            email=data.get('email', '') or '',
            first_name=data.get('first_name', '') or '',
            last_name=data.get('last_name', '') or '',
        )
        role_name = data.get('role')
        if role_name:
            role, _ = Role.objects.get_or_create(name=role_name)
            UserRole.objects.get_or_create(user=user, role=role)

        return Response({'message': 'Account created', 'user': self._get_user_data(user)}, status=201)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def deactivate(self, request, pk=None):
        """POST /api/users/{id}/deactivate/ -> disable a user account."""
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'message': 'User not found'}, status=404)
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response({'message': 'User deactivated', 'user': self._get_user_data(user)})

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def setup_2fa(self, request):
        user = request.user
        secret = pyotp.random_base32()
        TOTPDevice.objects.get_or_create(user=user, name='default', defaults={'key': secret})

        uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="Sales System")
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(uri)
        qr.make(fit=True)
        
        buffer = io.BytesIO()
        qr.make_image(fill_color="black", back_color="white").save(buffer, format='PNG')
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
        if not any(d.verify_token(request.data.get('code')) for d in devices_for_user(request.user)):
            return Response({'error': 'Invalid code'}, status=400)
        twofa, _ = User2FA.objects.get_or_create(user=request.user)
        twofa.is_enabled = True
        twofa.save()
        return Response({'message': '2FA enabled'})

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def disable_2fa(self, request):
        if not any(d.verify_token(request.data.get('code')) for d in devices_for_user(request.user)):
            return Response({'error': 'Invalid code'}, status=400)
        twofa = User2FA.objects.get(user=request.user)
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