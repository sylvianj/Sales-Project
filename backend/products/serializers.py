# products/serializers.py
from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

    # The POS frontend sends these field names; map them to the model's fields on write.
    WRITE_ALIASES = {
        'stock': 'stock_qty',
        'quantity': 'stock_qty',
        'tax': 'tax_rate',
        'cost_price': 'cost',
        'minimum_stock': 'reorder_level',
    }

    def to_internal_value(self, data):
        # Normalise incoming keys so the frontend's names land on the right model fields.
        data = data.dict() if hasattr(data, 'dict') else dict(data)
        for alias, real in self.WRITE_ALIASES.items():
            if alias in data and real not in data:
                data[real] = data[alias]
        return super().to_internal_value(data)

    def to_representation(self, instance):
        # Expose the extra field names the POS frontend reads.
        rep = super().to_representation(instance)
        price = float(instance.price) if instance.price is not None else 0
        rep['stock'] = instance.stock_qty
        rep['quantity'] = instance.stock_qty
        rep['tax'] = float(instance.tax_rate) if instance.tax_rate is not None else 0
        rep['minimum_stock'] = instance.reorder_level
        rep['cost_price'] = float(instance.cost) if instance.cost is not None else None
        # Model has a single price; mirror it to the tiered prices the UI expects.
        rep['wholesale_price'] = price
        rep['corporate_price'] = price
        rep['loyal_price'] = price
        return rep
