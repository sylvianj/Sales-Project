# sales/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Sale, SaleItem
from .serializers import SaleSerializer
from products.models import Product
from customers.models import Customer


def Home(request):
    return JsonResponse({'status': 'ok'})

class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _process_sale_items(items, data):
        """Validate and process sale items, return (items_data, subtotal) or error response."""
        subtotal, items_data = 0, []
        for item in items:
            product = get_object_or_404(Product, id=item.get('product_id'))
            qty = item['quantity']
            if product.stock_qty < qty:
                return None, Response({'error': f"Insufficient stock for {product.name}"}, status=400)
            
            line_total = float(product.price) * qty
            subtotal += line_total
            items_data.append({
                'product': product,
                'quantity': qty,
                'unit_price': product.price,
                'discount': item.get('discount', 0),
                'total': line_total
            })
        return (items_data, subtotal), None

    @transaction.atomic
    @action(detail=False, methods=['post'])
    def create_sale(self, request):
        data = request.data
        
        # Get customer
        customer = get_object_or_404(Customer, id=data.get('customer_id')) if data.get('customer_id') else None

        items = data.get('items', [])
        if not items:
            return Response({'error': 'At least one item required'}, status=400)

        # Process items
        result, error = self._process_sale_items(items, data)
        if error:
            return error
        items_data, subtotal = result

        # Calculate totals
        discount = float(data.get('discount', 0))
        tax = (subtotal - discount) * 0.16  # 16% tax
        grand_total = subtotal - discount + tax
        paid = float(data.get('paid_amount', 0))
        
        if paid < grand_total:
            return Response({'error': f'Insufficient payment. Required: {grand_total}'}, status=400)

        # Create sale
        sale = Sale.objects.create(
            customer=customer,
            cashier=request.user,
            subtotal=subtotal,
            discount=discount,
            tax_amount=tax,
            total=grand_total,
            paid_amount=paid,
            change_due=paid - grand_total,
            payment_method=data.get('payment_method', 'cash'),
            status='completed'
        )

        # Create sale items
        SaleItem.objects.bulk_create([
            SaleItem(
                sale=sale,
                product=item['product'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                discount=item['discount'],
                total=item['total']
            )
            for item in items_data
        ])

        # Build receipt
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
            'change': float(paid - grand_total)
        }
        return Response({'sale_id': sale.id, 'sale_no': sale.sale_no, 'receipt': receipt}, status=201)