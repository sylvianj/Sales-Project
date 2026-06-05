# products/suggestion_engine.py
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from .models import Product
from sales.models import SaleItem

def sales_velocity(product, days=30):
    start = timezone.now() - timedelta(days=days)
    sold = SaleItem.objects.filter(
        product=product,
        sale__sale_date__gte=start,
        sale__status='completed'
    ).aggregate(total=Sum('quantity'))['total'] or 0
    return sold / days

def parse_notes(notes):
    if not notes:
        return {}
    n = notes.lower()
    return {
        'high_demand': any(w in n for w in ['high', 'hot', 'fast', 'rush']),
        'low_demand': any(w in n for w in ['slow', 'cold', 'dead']),
        'promotion': any(w in n for w in ['promo', 'sale', 'discount']),
        'supplier_issue': any(w in n for w in ['delay', 'shortage', 'backorder']),
        'seasonal': any(w in n for w in ['season', 'holiday', 'summer', 'winter']),
    }

def generate_suggestion(product):
    stock = product.stock_qty
    reorder_lvl = product.reorder_level
    reorder_qty = product.reorder_qty
    vel = sales_velocity(product)
    days_left = stock / vel if vel > 0 else 999

    suggested = 0
    reasons = []

    if stock <= reorder_lvl:
        reasons.append(f"Stock ({stock}) ≤ reorder level ({reorder_lvl}).")
        suggested = max(reorder_qty, int(vel * 14))
    if days_left < 7:
        reasons.append(f"Will last only {days_left:.1f} days at current sales rate.")
        if suggested == 0:
            suggested = int(vel * 14)

    notes = parse_notes(product.store_keeper_notes)
    if notes.get('high_demand'):
        reasons.append("Store notes indicate high demand.")
        suggested = int(suggested * 1.5)
    if notes.get('low_demand'):
        reasons.append("Store notes indicate slow moving product.")
        suggested = int(suggested * 0.7)
    if notes.get('promotion'):
        reasons.append("Promotion active – increase order.")
        suggested = int(suggested * 1.3)
    if notes.get('supplier_issue'):
        reasons.append("Supplier delay mentioned – order extra buffer.")
        suggested = int(suggested * 1.2)
    if notes.get('seasonal'):
        reasons.append("Seasonal product – adjust order accordingly.")
        suggested = int(suggested * 1.2)

    if not reasons:
        reasons.append("Stock is adequate. No urgent reorder needed.")
        suggested = 0

    return {
        'product_id': product.id,
        'product_name': product.name,
        'current_stock': stock,
        'avg_daily_sales': round(vel, 2),
        'days_until_out': round(days_left, 1),
        'suggested_order': suggested,
        'reason': ' '.join(reasons)
    }

def update_all_suggestions():
    for product in Product.objects.filter(is_active=True):
        sug = generate_suggestion(product)
        product.suggested_order_quantity = sug['suggested_order']
        product.suggestion_reason = sug['reason']
        product.last_suggestion_generated = timezone.now()
        product.save(update_fields=['suggested_order_quantity', 'suggestion_reason', 'last_suggestion_generated'])
    return Product.objects.filter(is_active=True).count()