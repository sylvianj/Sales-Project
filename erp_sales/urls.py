# erp_sales/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from sales.views import SaleViewSet
from products.views import ProductViewSet
from customers.views import CustomerViewSet
from users.views import AuthViewSet
from returns.views import ReturnViewSet

router = DefaultRouter()
router.register(r'sales', SaleViewSet)
router.register(r'products', ProductViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'returns', ReturnViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]