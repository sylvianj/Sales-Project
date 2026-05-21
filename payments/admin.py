# payments/admin.py
from django.contrib import admin
from .models import Payment, Receipt

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'sale', 'amount_paid', 'payment_method', 'payment_date']
    search_fields = ['sale__sale_no']

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['id', 'receipt_no', 'sale', 'printed', 'created_at']