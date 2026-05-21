# returns/admin.py
from django.contrib import admin
from .models import Return

@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ['id', 'return_no', 'sale', 'product', 'quantity', 'refund_amount', 'status']
    list_filter = ['status', 'return_type']
    search_fields = ['return_no', 'sale__sale_no']