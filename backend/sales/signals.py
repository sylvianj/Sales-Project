# sales/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import SaleItem
from products.utils import send_low_stock_alert
from products.models import Product

@receiver(post_save, sender=SaleItem)
def reduce_stock_on_sale(sender, instance, created, **kwargs):
    if created:
        product = instance.product
        product.stock_qty -= instance.quantity
        product.save(update_fields=['stock_qty'])
        if product.stock_qty <= product.reorder_level:
            send_low_stock_alert(product)

@receiver(post_delete, sender=SaleItem)
def restore_stock_on_sale_delete(sender, instance, **kwargs):
    product = instance.product
    product.stock_qty += instance.quantity
    product.save(update_fields=['stock_qty'])