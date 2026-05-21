# products/admin.py
from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'sku', 'name', 'price', 'stock_qty', 'is_active']
    search_fields = ['sku', 'name']
    list_editable = ['price', 'stock_qty', 'is_active']
    list_filter = ['is_active']  # REMOVED 'category' - it doesn't exist