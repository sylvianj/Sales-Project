# payments/models.py
from django.db import models
from django.contrib.auth.models import User
from sales.models import Sale
import uuid

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    change_given = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.payment_method} - {self.amount_paid}"

    class Meta:
        db_table = 'payments'


class Receipt(models.Model):
    sale = models.OneToOneField(Sale, on_delete=models.CASCADE, related_name='receipt')
    receipt_no = models.CharField(max_length=50, unique=True, blank=True)
    receipt_html = models.TextField(blank=True, null=True)
    printed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.receipt_no:
            self.receipt_no = f"REC-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Receipt {self.receipt_no}"

    class Meta:
        db_table = 'receipts'