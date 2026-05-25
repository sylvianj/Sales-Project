# returns/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from sales.models import Sale
from products.models import Product
import uuid

class Return(models.Model):
    RETURN_TYPES = [
        ('full', 'Full Return'),
        ('partial', 'Partial Return'),
        ('exchange', 'Exchange'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    DIRECTION_CHOICES = [
        ('customer', 'Customer Return (add stock)'),
        ('supplier', 'Supplier Return (remove stock)'),
    ]

    return_no = models.CharField(max_length=20, unique=True, blank=True)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, blank=True, null=True)  # nullable for supplier returns
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # optional for supplier
    reason = models.TextField(blank=True, null=True)
    return_type = models.CharField(max_length=20, choices=RETURN_TYPES, default='full')
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default='customer')
    processed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    return_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.return_no:
            self.return_no = f"RET-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.return_no} ({self.get_direction_display()})"

    class Meta:
        db_table = 'returns'