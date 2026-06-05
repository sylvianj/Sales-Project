from django.urls import path
from payments.views import lipa_na_mpesa, MpesaCallbackView

urlpatterns = [
    path('mpesa/', lipa_na_mpesa, name='lipa_na_mpesa'),
    path('callback/', MpesaCallbackView.as_view(), name='mpesa_callback'),
]
