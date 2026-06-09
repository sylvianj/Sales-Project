# products/excel_urls.py
from django.urls import path
from .excel_views import ProductExcelImportView, ProductTemplateView

urlpatterns = [
    path('import/products/', ProductExcelImportView.as_view(), name='excel_import_products'),
    path('template/products/', ProductTemplateView.as_view(), name='excel_template_products'),
]
