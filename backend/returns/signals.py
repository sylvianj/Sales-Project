# returns/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Return

@receiver(post_save, sender=Return)
def handle_stock_on_return(sender, instance, created, **kwargs):
    if created and instance.status == 'completed':
        product = instance.product
        if instance.direction == 'customer':
            # Customer return → add stock back
            product.stock_qty += instance.quantity
        else:
            # Supplier return → remove stock (send back to supplier)
            product.stock_qty -= instance.quantity
        product.save(update_fields=['stock_qty'])