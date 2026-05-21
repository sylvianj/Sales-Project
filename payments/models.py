# payments/models.py
from django.db import models
from django.contrib.auth.models import User
from sales.models import Sale
import uuid

class Payment(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    change_given = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20)
    payment_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.payment_method} - {self.amount_paid}"
    
    class Meta:
        db_table = 'payments'

class Receipt(models.Model):
    sale = models.OneToOneField(Sale, on_delete=models.CASCADE)
    receipt_no = models.CharField(max_length=50, unique=True, blank=True)
    printed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.receipt_no:
            self.receipt_no = f"REC-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'receipts'