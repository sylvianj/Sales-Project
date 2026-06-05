from django.contrib import admin
from .models import MpesaAccount, MpesaTransaction, MpesaCallbackLog, MpesaReconciliation, PaymentAccount, ExpenseCategory, Expense, PaymentTransaction

@admin.register(MpesaAccount)
class MpesaAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'shortcode', 'is_active']

@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'amount', 'phone_number', 'status', 'created_at']
    list_filter = ['status', 'transaction_type']

@admin.register(MpesaCallbackLog)
class MpesaCallbackLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'received_at']

@admin.register(MpesaReconciliation)
class MpesaReconciliationAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'reconciled_at', 'reconciled_by']

@admin.register(PaymentAccount)
class PaymentAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_type', 'account_number', 'is_active']

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['category', 'amount', 'date', 'created_by']
    list_filter = ['category', 'date']

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['sale', 'payment_account', 'amount', 'transaction_date']