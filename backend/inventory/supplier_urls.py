# inventory/supplier_urls.py  -> mounted at /api/suppliers/
from rest_framework.routers import DefaultRouter
from .views import SupplierViewSet

router = DefaultRouter()
router.register(r'', SupplierViewSet, basename='supplier-top')

urlpatterns = router.urls
