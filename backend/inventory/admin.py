from django.contrib import admin
from .models import Supplier, Batch

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'email']
    search_fields = ['name', 'contact_person']

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['batch_no', 'product', 'supplier', 'quantity', 'expiry_date']
    list_filter = ['product', 'supplier']