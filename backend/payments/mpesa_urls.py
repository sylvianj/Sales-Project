# payments/mpesa_urls.py  -> mounted at /api/mpesa-transactions/
from django.urls import path
from .mpesa_views import stk_push, verify_transaction, simulate_callback, mpesa_callback

urlpatterns = [
    path('stk-push/', stk_push, name='mpesa_stk_push'),
    path('callback/', mpesa_callback, name='mpesa_callback_v2'),
    path('<int:pk>/verify/', verify_transaction, name='mpesa_verify'),
    path('<int:pk>/simulate-callback/', simulate_callback, name='mpesa_simulate_callback'),
]
