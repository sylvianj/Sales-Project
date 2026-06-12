# payments/mpesa_views.py
"""M-Pesa STK push for the POS frontend.

If Daraja credentials are configured in .env, this sends a REAL STK push that
prompts the customer's phone. If credentials are missing, it falls back to a
SIMULATED flow so the UI still works in development.
Lifecycle: stk-push (pending) -> callback / verify -> success|failed.
"""
import base64
import uuid
from datetime import datetime

import requests
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import MpesaTransaction, MpesaCallbackLog
from .utils import format_phone_number


# ---------------------------------------------------------------------------
# Daraja helpers
# ---------------------------------------------------------------------------
def _cfg():
    return getattr(settings, 'MPESA_CONFIG', {}) or {}


def _credentials_ready():
    c = _cfg()
    return all(c.get(k) for k in ['MPESA_CONSUMER_KEY', 'MPESA_CONSUMER_SECRET',
                                   'MPESA_SHORTCODE', 'MPESA_PASSKEY'])


def _base_url():
    env = (_cfg().get('MPESA_ENVIRONMENT') or 'sandbox').lower()
    return 'https://api.safaricom.co.ke' if env == 'production' else 'https://sandbox.safaricom.co.ke'


def _access_token():
    c = _cfg()
    resp = requests.get(
        f'{_base_url()}/oauth/v1/generate?grant_type=client_credentials',
        auth=(c['MPESA_CONSUMER_KEY'], c['MPESA_CONSUMER_SECRET']),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()['access_token']


def _callback_url():
    return getattr(settings, 'MPESA_CALLBACK_URL', None) \
        or 'https://example.com/api/mpesa-transactions/callback/'


def _tx_data(tx):
    return {
        'id': tx.id,
        'transaction_id': tx.transaction_id,
        'transaction_type': tx.transaction_type,
        'amount': float(tx.amount),
        'phone_number': tx.phone_number,
        'account_reference': tx.account_reference,
        'status': tx.status,
        'result_code': tx.result_code,
        'result_desc': tx.result_desc,
        'checkout_request_id': tx.checkout_request_id,
        'receipt_number': tx.receipt_number,
        'created_at': tx.created_at,
    }


def _resolve(tx, status):
    success = str(status).lower() in ('success', 'completed', 'paid', '1', 'true')
    if success:
        tx.status = 'success'
        tx.result_code = 0
        tx.result_desc = 'The service request is processed successfully.'
        tx.receipt_number = tx.receipt_number or f'R{uuid.uuid4().hex[:10].upper()}'
    else:
        tx.status = 'failed'
        tx.result_code = 1032
        tx.result_desc = 'Request cancelled by user.'
    tx.save()
    return tx


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stk_push(request):
    try:
        amount = int(float(request.data.get('amount') or 0))
    except (TypeError, ValueError):
        return Response({'success': False, 'message': 'Invalid amount'}, status=400)
    if amount < 1:
        return Response({'success': False, 'message': 'Amount must be at least 1'}, status=400)

    phone_raw = request.data.get('phone_number') or ''
    account_reference = str(request.data.get('account_reference') or f'POS-{uuid.uuid4().hex[:8]}')

    # ---- SIMULATED fallback (no credentials) ----
    if not _credentials_ready():
        tx = MpesaTransaction.objects.create(
            transaction_id=f'SIM-{uuid.uuid4().hex[:12].upper()}',
            transaction_type='stk_push',
            amount=amount,
            phone_number=str(phone_raw),
            account_reference=account_reference,
            checkout_request_id=f'ws_CO_{uuid.uuid4().hex[:16]}',
            status='pending',
            result_desc='SIMULATED STK push (no Daraja credentials configured).',
        )
        data = _tx_data(tx)
        return Response({
            'success': True, 'simulated': True,
            'message': 'Simulated STK push (configure Daraja credentials in .env for a real prompt).',
            'transaction': data, **data,
        }, status=201)

    # ---- REAL Daraja STK push ----
    try:
        phone = format_phone_number(phone_raw)
        c = _cfg()
        shortcode = c['MPESA_SHORTCODE']
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(f'{shortcode}{c["MPESA_PASSKEY"]}{timestamp}'.encode()).decode()

        payload = {
            'BusinessShortCode': shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': amount,
            'PartyA': phone,
            'PartyB': shortcode,
            'PhoneNumber': phone,
            'CallBackURL': _callback_url(),
            'AccountReference': account_reference[:12],
            'TransactionDesc': 'POS payment',
        }
        resp = requests.post(
            f'{_base_url()}/mpesa/stkpush/v1/processrequest',
            json=payload,
            headers={'Authorization': f'Bearer {_access_token()}'},
            timeout=30,
        )
        body = resp.json()
    except Exception as exc:
        return Response({'success': False, 'message': f'M-Pesa request failed: {exc}'}, status=502)

    if str(body.get('ResponseCode')) == '0':
        tx = MpesaTransaction.objects.create(
            transaction_id=body.get('CheckoutRequestID') or f'STK-{uuid.uuid4().hex[:10]}',
            transaction_type='stk_push',
            amount=amount,
            phone_number=phone,
            account_reference=account_reference,
            checkout_request_id=body.get('CheckoutRequestID', ''),
            status='pending',
            result_desc=body.get('CustomerMessage', 'STK push sent. Enter your M-Pesa PIN.'),
        )
        data = _tx_data(tx)
        return Response({
            'success': True, 'simulated': False,
            'message': body.get('CustomerMessage', 'STK push sent. Check your phone.'),
            'transaction': data, **data,
        }, status=201)

    return Response({
        'success': False,
        'message': body.get('errorMessage') or body.get('ResponseDescription') or 'STK push failed',
        'daraja': body,
    }, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_transaction(request, pk):
    try:
        tx = MpesaTransaction.objects.get(pk=pk)
    except MpesaTransaction.DoesNotExist:
        return Response({'success': False, 'message': 'Transaction not found'}, status=404)
    tx = _resolve(tx, request.data.get('status', 'success'))
    data = _tx_data(tx)
    return Response({'success': tx.status == 'success', 'transaction': data, **data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def simulate_callback(request, pk):
    try:
        tx = MpesaTransaction.objects.get(pk=pk)
    except MpesaTransaction.DoesNotExist:
        return Response({'success': False, 'message': 'Transaction not found'}, status=404)
    status = request.data.get('status', 'success')
    tx = _resolve(tx, status)
    MpesaCallbackLog.objects.create(transaction=tx, raw_data={'simulated': True, 'status': status})
    data = _tx_data(tx)
    return Response({'success': tx.status == 'success', 'transaction': data, **data})


@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_callback(request):
    """Safaricom POSTs the real result here (needs a public URL, e.g. ngrok)."""
    cb = (request.data or {}).get('Body', {}).get('stkCallback', {})
    checkout_id = cb.get('CheckoutRequestID')
    result_code = cb.get('ResultCode')
    try:
        tx = MpesaTransaction.objects.get(checkout_request_id=checkout_id)
        MpesaCallbackLog.objects.create(transaction=tx, raw_data=request.data)
        if result_code == 0:
            items = {i.get('Name'): i.get('Value') for i in cb.get('CallbackMetadata', {}).get('Item', [])}
            tx.status = 'success'
            tx.result_code = 0
            tx.result_desc = cb.get('ResultDesc', 'Success')
            tx.receipt_number = items.get('MpesaReceiptNumber', '')
        else:
            tx.status = 'failed'
            tx.result_code = result_code
            tx.result_desc = cb.get('ResultDesc', 'Failed')
        tx.save()
    except MpesaTransaction.DoesNotExist:
        pass
    # Safaricom expects this exact acknowledgement
    return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_config(request):
    return Response({
        'mpesa': {
            'enabled': _credentials_ready(),
            'environment': _cfg().get('MPESA_ENVIRONMENT') or 'sandbox',
            'shortcode': _cfg().get('MPESA_SHORTCODE') or '',
            'simulated': not _credentials_ready(),
        },
        'currency': 'KES',
        'tax_rate': 16,
    })
