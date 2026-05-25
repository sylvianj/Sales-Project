# returns/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Return
from .serializers import ReturnSerializer
from sales.models import Sale, SaleItem
from products.models import Product


class ReturnViewSet(viewsets.ModelViewSet):
    queryset = Return.objects.all()
    serializer_class = ReturnSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    @action(detail=False, methods=['post'])
    def process(self, request):
        """
        Process a return.
        For customer return: requires sale_id, product_id, quantity, refund_amount.
        For supplier return: requires product_id, quantity (sale_id not required, refund_amount optional).
        """
        direction = request.data.get('direction', 'customer')
        if direction not in ['customer', 'supplier']:
            return Response({'error': 'Invalid direction. Must be "customer" or "supplier".'},
                            status=status.HTTP_400_BAD_REQUEST)

        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')
        if not product_id or not quantity:
            return Response({'error': 'Product and quantity are required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

        quantity = int(quantity)
        if quantity <= 0:
            return Response({'error': 'Quantity must be positive.'}, status=status.HTTP_400_BAD_REQUEST)

        # For customer returns, we need a sale and check if the product was actually sold
        sale = None
        refund_amount = request.data.get('refund_amount')

        if direction == 'customer':
            sale_id = request.data.get('sale_id')
            if not sale_id:
                return Response({'error': 'Customer returns require sale_id.'},
                                status=status.HTTP_400_BAD_REQUEST)
            try:
                sale = Sale.objects.get(id=sale_id)
            except Sale.DoesNotExist:
                return Response({'error': 'Sale not found.'}, status=status.HTTP_404_NOT_FOUND)

            # Verify product was in the sale and check maximum returnable quantity
            sale_item = SaleItem.objects.filter(sale=sale, product=product).first()
            if not sale_item:
                return Response({'error': 'Product not found in the given sale.'},
                                status=status.HTTP_400_BAD_REQUEST)
            if quantity > sale_item.quantity:
                return Response({'error': f'Cannot return more than sold. Sold: {sale_item.quantity}'},
                                status=status.HTTP_400_BAD_REQUEST)

            # If refund_amount not provided, calculate from unit price
            if refund_amount is None:
                refund_amount = float(sale_item.unit_price) * quantity

        else:  # supplier return
            # For supplier returns, refund amount is optional (e.g., not refunded)
            if refund_amount is None:
                refund_amount = 0  # or None if you prefer null

        # Create the return record
        return_obj = Return.objects.create(
            sale=sale,
            product=product,
            quantity=quantity,
            refund_amount=refund_amount,
            reason=request.data.get('reason', ''),
            return_type=request.data.get('return_type', 'full'),
            direction=direction,
            processed_by=request.user,
            status='completed'   # auto-approve for simplicity; could be 'pending' with admin approval
        )

        # Stock is adjusted automatically by the signal (returns/signals.py)
        # For customer returns: stock increases; for supplier returns: stock decreases.

        return Response({
            'return_id': return_obj.id,
            'return_no': return_obj.return_no,
            'refund_amount': float(refund_amount),
            'direction': direction,
            'message': 'Return processed successfully'
        }, status=status.HTTP_201_CREATED)