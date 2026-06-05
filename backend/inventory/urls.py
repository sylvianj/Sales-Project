from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupplierViewSet, BatchViewSet

router = DefaultRouter()
router.register(r'', SupplierViewSet, basename='supplier')
router.register(r'batches', BatchViewSet, basename='batch')

urlpatterns = [
    path('', include(router.urls)),
]
