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

# payments/models.py
# Add to your Payment model...
checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
status = models.CharField(max_length=20, default='pending')  # pending, completed, failed

class MpesaAccount(models.Model):
    shortcode = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    consumer_key = models.CharField(max_length=100)
    consumer_secret = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.shortcode})"


class MpesaTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('stk_push', 'STK Push'),
        ('c2b', 'Customer to Business'),
        ('b2c', 'Business to Customer'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    transaction_id = models.CharField(max_length=100, unique=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15)
    account_reference = models.CharField(max_length=100)
    result_code = models.IntegerField(null=True, blank=True)
    result_desc = models.CharField(max_length=200, blank=True)
    checkout_request_id = models.CharField(max_length=100, blank=True)
    receipt_number = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_id} - {self.amount}"


class MpesaCallbackLog(models.Model):
    transaction = models.ForeignKey(MpesaTransaction, on_delete=models.CASCADE, null=True)
    raw_data = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Callback at {self.received_at}"


class MpesaReconciliation(models.Model):
    transaction = models.ForeignKey(MpesaTransaction, on_delete=models.CASCADE)
    reconciled_with = models.CharField(max_length=100)  # e.g., bank statement reference
    reconciled_at = models.DateTimeField(auto_now_add=True)
    reconciled_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Reconciliation for {self.transaction}"


class PaymentAccount(models.Model):
    ACCOUNT_TYPES = [
        ('bank', 'Bank Account'),
        ('mobile', 'Mobile Money'),
        ('cash', 'Cash'),
    ]
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    account_number = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Expense Categories'

    def __str__(self):
        return self.name


class Expense(models.Model):
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    date = models.DateField()
    receipt = models.FileField(upload_to='expenses/', blank=True, null=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category.name} - {self.amount}"


class PaymentTransaction(models.Model):
    sale = models.ForeignKey('sales.Sale', on_delete=models.CASCADE, null=True, blank=True)
    payment_account = models.ForeignKey(PaymentAccount, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='completed')

    def __str__(self):
        return f"{self.payment_account.name} - {self.amount}"