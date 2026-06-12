# erp_sales/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.http import HttpResponseRedirect

from sales.views import Home
from payments.mpesa_views import payment_config




urlpatterns = [
    path('admin/', admin.site.urls),

    # Health / status endpoints
    path('health/', Home, name='health'),
    
    # API Routes
    path('api/customers/', include('customers.urls')),
    path('api/users/', include('users.urls')),
    path('api/products/', include('products.urls')),
    path('api/sales/', include('sales.urls')),
    path('api/returns/', include('returns.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/excel/', include('products.excel_urls')),

    # POS frontend compatibility routes
    path('api/suppliers/', include('inventory.supplier_urls')),
    path('api/mpesa-transactions/', include('payments.mpesa_urls')),
    path('api/payment-notifications/', include('notifications.urls')),
    path('api/react/payment-config/', payment_config, name='react_payment_config'),

    # Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]