# customers/admin.py
from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'phone', 'email', 'account_ref', 'loyalty_points']
    search_fields = ['name', 'phone', 'email', 'account_ref']
    list_filter = ['created_at']