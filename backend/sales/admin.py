# sales/admin.py
from django.contrib import admin
from .models import Sale, SaleItem

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    readonly_fields = ['total']

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['id', 'sale_no', 'sale_date', 'customer', 'cashier', 'total', 'status']
    search_fields = ['sale_no', 'customer__name']
    list_filter = ['status', 'payment_method', 'sale_date']
    readonly_fields = ['sale_no', 'subtotal', 'tax_amount', 'total', 'change_due']
    inlines = [SaleItemInline]

@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'sale', 'product', 'quantity', 'unit_price', 'total']