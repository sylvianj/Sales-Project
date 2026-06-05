# products/models.py
from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=16.00)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    stock_qty = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=5)
    reorder_qty = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)

    # New fields for store keeper notes & suggestions
    store_keeper_notes = models.TextField(blank=True, null=True, help_text="e.g., high demand, supplier delay")
    suggested_order_quantity = models.IntegerField(blank=True, null=True)
    suggestion_reason = models.TextField(blank=True, null=True)
    last_suggestion_generated = models.DateTimeField(blank=True, null=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sku} - {self.name}"

    class Meta:
        db_table = 'products'
        ordering = ['name']