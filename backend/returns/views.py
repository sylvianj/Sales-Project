# returns/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Return
from .serializers import ReturnSerializer
from sales.models import Sale, SaleItem
from products.models import Product

class ReturnViewSet(viewsets.ModelViewSet):
    queryset = Return.objects.all()
    serializer_class = ReturnSerializer
    permission_classes = [IsAuthenticated]

    def _validate_return_data(self, data):
        """Validate and return (product, quantity, error_response or None)."""
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        
        if not product_id or not quantity:
            return None, None, Response({'error': 'Product and quantity are required.'}, status=400)
        
        product = get_object_or_404(Product, id=product_id)
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return None, None, Response({'error': 'Quantity must be a positive number.'}, status=400)
        
        return product, quantity, None

    @transaction.atomic
    @action(detail=False, methods=['post'])
    def process(self, request):
        """Process a return (customer or supplier)."""
        direction = request.data.get('direction', 'customer')
        if direction not in ['customer', 'supplier']:
            return Response({'error': 'Invalid direction. Must be "customer" or "supplier".'}, status=400)

        product, quantity, error = self._validate_return_data(request.data)
        if error:
            return error

        sale = None
        refund_amount = request.data.get('refund_amount')

        if direction == 'customer':
            sale_id = request.data.get('sale_id')
            if not sale_id:
                return Response({'error': 'Customer returns require sale_id.'}, status=400)
            
            sale = get_object_or_404(Sale, id=sale_id)

            # Verify product in sale and check returnable quantity
            sale_item = SaleItem.objects.filter(sale=sale, product=product).first()
            if not sale_item:
                return Response({'error': 'Product not found in the given sale.'}, status=400)
            if quantity > sale_item.quantity:
                return Response({'error': f'Cannot return more than sold. Sold: {sale_item.quantity}'}, status=400)

            # Auto-calculate refund if not provided
            if refund_amount is None:
                refund_amount = float(sale_item.unit_price) * quantity
        else:
            # Supplier return - optional refund
            if refund_amount is None:
                refund_amount = 0

        # Create return record
        return_obj = Return.objects.create(
            sale=sale,
            product=product,
            quantity=quantity,
            refund_amount=refund_amount,
            reason=request.data.get('reason', ''),
            return_type=request.data.get('return_type', 'full'),
            direction=direction,
            processed_by=request.user,
            status='completed'
        )

        return Response({
            'return_id': return_obj.id,
            'return_no': return_obj.return_no,
            'refund_amount': float(refund_amount),
            'direction': direction,
            'message': 'Return processed successfully'
        }, status=201)