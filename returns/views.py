# returns/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Return
from sales.models import Sale, SaleItem
from products.models import Product

class ReturnViewSet(viewsets.ModelViewSet):
    queryset = Return.objects.all()
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    @action(detail=False, methods=['post'])
    def process_return(self, request):
        """Process a product return"""
        sale_id = request.data.get('sale_id')
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')
        reason = request.data.get('reason', '')
        
        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return Response({'error': 'Sale not found'}, status=404)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=404)
        
        # Check if product was in the sale
        sale_item = SaleItem.objects.filter(sale=sale, product=product).first()
        if not sale_item:
            return Response({'error': 'Product not found in this sale'}, status=400)
        
        if quantity > sale_item.quantity:
            return Response({'error': f'Cannot return more than sold. Sold: {sale_item.quantity}'}, status=400)
        
        # Calculate refund amount
        refund_amount = float(sale_item.unit_price) * quantity
        
        # Create return record
        return_obj = Return.objects.create(
            sale=sale,
            product=product,
            quantity=quantity,
            refund_amount=refund_amount,
            reason=reason,
            processed_by=request.user,
            status='completed'
        )
        
        # Update stock
        product.stock_qty += quantity
        product.save()
        
        return Response({
            'return_id': return_obj.id,
            'return_no': return_obj.return_no,
            'refund_amount': refund_amount,
            'message': 'Return processed successfully'
        }, status=status.HTTP_201_CREATED)