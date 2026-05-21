# erp_sales/urls.py - COMPLETE FILE
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from sales.views import SaleViewSet
from products.views import ProductViewSet
from customers.views import CustomerViewSet
from users.views import AuthViewSet

router = DefaultRouter()
router.register(r'sales', SaleViewSet)
router.register(r'products', ProductViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]