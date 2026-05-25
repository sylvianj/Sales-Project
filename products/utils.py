# products/utils.py
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import F
from .models import Product
from users.models import UserRole

def send_low_stock_alert(product):
    users = UserRole.objects.filter(role__name__in=['store_keeper', 'administrator']).select_related('user')
    recipient_list = [ur.user.email for ur in users if ur.user.email]
    if not recipient_list:
        return
    subject = f"⚠️ LOW STOCK ALERT: {product.name}"
    message = f"""
    Product: {product.name}
    SKU: {product.sku}
    Current Stock: {product.stock_qty}
    Reorder Level: {product.reorder_level}
    Suggested Order: {product.reorder_qty} units
    """
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)

def check_all_low_stock():
    low_stock = Product.objects.filter(stock_qty__lte=F('reorder_level'), is_active=True)
    for p in low_stock:
        send_low_stock_alert(p)
    return low_stock.count()