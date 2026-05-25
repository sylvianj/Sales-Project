# sales/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Sale, SaleItem
from .serializers import SaleSerializer
from products.models import Product
from customers.models import Customer

class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    @action(detail=False, methods=['post'])
    def create_sale(self, request):
        data = request.data
        customer_id = data.get('customer_id')
        try:
            customer = Customer.objects.get(id=customer_id) if customer_id else None
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=404)

        items = data.get('items', [])
        if not items:
            return Response({'error': 'At least one item required'}, status=400)

        subtotal = 0
        items_data = []
        for item in items:
            try:
                product = Product.objects.get(id=item['product_id'])
            except Product.DoesNotExist:
                return Response({'error': f"Product {item['product_id']} not found"}, status=404)
            qty = item['quantity']
            if product.stock_qty < qty:
                return Response({'error': f"Insufficient stock for {product.name}"}, status=400)
            line_total = float(product.price) * qty
            subtotal += line_total
            items_data.append({
                'product': product,
                'quantity': qty,
                'unit_price': product.price,
                'discount': item.get('discount', 0),
                'total': line_total
            })

        discount = float(data.get('discount', 0))
        after_discount = subtotal - discount
        tax_rate = 16
        tax = after_discount * (tax_rate / 100)
        grand_total = after_discount + tax
        paid = float(data.get('paid_amount', 0))
        change = paid - grand_total
        if change < 0:
            return Response({'error': f'Insufficient payment. Required: {grand_total}'}, status=400)

        sale = Sale.objects.create(
            customer=customer,
            cashier=request.user,
            subtotal=subtotal,
            discount=discount,
            tax_amount=tax,
            total=grand_total,
            paid_amount=paid,
            change_due=change,
            payment_method=data.get('payment_method', 'cash'),
            status='completed'
        )

        for item in items_data:
            SaleItem.objects.create(
                sale=sale,
                product=item['product'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                discount=item['discount'],
                total=item['total']
            )
            # Stock is reduced by signal, but we also need to decrement here because signal triggers on creation
            # Actually signal already does it, but we must ensure stock is updated before next iteration.
            # The signal is already called inside SaleItem creation. So no extra save needed.
            # However to avoid double reduction, we do nothing extra.
            pass

        receipt = {
            'sale_no': sale.sale_no,
            'date': sale.sale_date.strftime('%Y-%m-%d %H:%M:%S'),
            'cashier': sale.cashier.username,
            'customer': sale.customer.name if sale.customer else 'Walk-in',
            'items': [
                {'name': i['product'].name, 'quantity': i['quantity'], 'unit_price': float(i['unit_price']), 'total': float(i['total'])}
                for i in items_data
            ],
            'subtotal': float(subtotal),
            'discount': float(discount),
            'tax': float(tax),
            'total': float(grand_total),
            'paid': float(paid),
            'change': float(change)
        }
        return Response({'sale_id': sale.id, 'sale_no': sale.sale_no, 'receipt': receipt}, status=201)