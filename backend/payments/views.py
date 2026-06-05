# payments/views.py
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from .models import Payment
from .utils import format_phone_number

logger = logging.getLogger(__name__)

# Try to import M-Pesa classes
try:
    from django_daraja.access_token import MpesaAccessToken
    from django_daraja.mpesa import MpesaExpress
    MPESA_AVAILABLE = True
except (ImportError, AttributeError):
    try:
        # Fallback import path
        from django_daraja import MpesaAccessToken, MpesaExpress
        MPESA_AVAILABLE = True
    except (ImportError, AttributeError):
        MPESA_AVAILABLE = False
        logger.warning("M-Pesa integration not available. Ensure django_daraja is properly installed and configured.")

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def lipa_na_mpesa(request):
    """Initiate M-Pesa STK Push payment."""
    if not MPESA_AVAILABLE:
        return Response({
            'error': 'M-Pesa integration not configured',
            'message': 'Please ensure django_daraja is properly installed and M-Pesa credentials are set in environment variables'
        }, status=503)
    
    phone_number = request.data.get('phone_number')
    amount = request.data.get('amount')

    if not phone_number or not amount:
        return Response({'error': 'Phone number and amount are required.'}, status=400)

    try:
        amount = int(amount)
    except ValueError:
        return Response({'error': 'Amount must be a number.'}, status=400)

    try:
        formatted_phone = format_phone_number(phone_number)
        access_token = MpesaAccessToken().access_token
        
        mpesa_express = MpesaExpress()
        response = mpesa_express.stk_push(
            phone_number=formatted_phone,
            amount=amount,
            account_reference=request.data.get('account_reference', 'SalesPayment'),
            transaction_desc=request.data.get('transaction_desc', 'Payment for goods'),
            callback_url=getattr(settings, 'MPESA_CALLBACK_URL', 'https://your-domain.com/api/payments/callback/')
        )

        logger.info(f"M-Pesa STK Push: {response.get('ResponseCode', 'N/A')}")

        if response.get('ResponseCode') == '0':
            return Response({
                'message': 'STK Push sent successfully.',
                'checkout_request_id': response.get('CheckoutRequestID')
            }, status=200)
        
        return Response({
            'error': 'Failed to send STK Push.',
            'details': response.get('errorMessage', 'Unknown error')
        }, status=400)
    
    except Exception as e:
        logger.error(f"M-Pesa error: {str(e)}")
        return Response({'error': 'M-Pesa payment failed', 'details': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class MpesaCallbackView(APIView):
    """Handle M-Pesa callback after payment."""
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        if not data:
            return Response({"ResultCode": 1, "ResultDesc": "Invalid JSON or empty payload"}, status=400)

        stk_callback = data.get('Body', {}).get('stkCallback', {})
        result_code = stk_callback.get('ResultCode')
        checkout_request_id = stk_callback.get('CheckoutRequestID')

        if result_code != 0:
            logger.warning(f"Payment failed: {checkout_request_id}, Code: {result_code}")
            return Response({"ResultCode": 0, "ResultDesc": "Success"})

        # Extract metadata
        items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
        amount = next((item.get('Value') for item in items if item.get('Name') == 'Amount'), None)
        receipt_number = next((item.get('Value') for item in items if item.get('Name') == 'MpesaReceiptNumber'), None)

        # Update payment record
        try:
            payment = Payment.objects.get(checkout_request_id=checkout_request_id)
            payment.amount_paid = amount
            payment.payment_reference = receipt_number
            payment.payment_method = 'mpesa'
            payment.status = 'completed'
            payment.save()
            
            if payment.sale:
                payment.sale.status = 'completed'
                payment.sale.save()
            
            logger.info(f"Payment completed: {checkout_request_id}, Amount: {amount}")
        except Payment.DoesNotExist:
            logger.error(f"Payment record not found: {checkout_request_id}")

        return Response({"ResultCode": 0, "ResultDesc": "Success"})