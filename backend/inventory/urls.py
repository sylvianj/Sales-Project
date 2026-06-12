from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupplierViewSet, BatchViewSet, stock_adjust

router = DefaultRouter()
router.register(r'batches', BatchViewSet, basename='batch')
router.register(r'', SupplierViewSet, basename='supplier')

urlpatterns = [
    path('adjust/', stock_adjust, name='stock_adjust'),
    path('', include(router.urls)),
]
