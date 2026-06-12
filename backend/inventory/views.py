from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Supplier, Batch
from .serializers import SupplierSerializer, BatchSerializer
from products.models import Product
from products.serializers import ProductSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stock_adjust(request):
    """POST /api/inventory/adjust/ -> change a product's stock and return the updated product."""
    product_id = request.data.get('product_id')
    movement_type = request.data.get('movement_type', 'adjustment')
    try:
        qty = int(float(request.data.get('quantity', 0)))
    except (TypeError, ValueError):
        return Response({'success': False, 'message': 'Invalid quantity'}, status=400)

    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return Response({'success': False, 'message': 'Product not found'}, status=404)

    if movement_type == 'stock_in':
        product.stock_qty += qty
    elif movement_type == 'stock_out':
        product.stock_qty = max(0, product.stock_qty - qty)
    else:  # 'adjustment' -> set to an absolute value
        product.stock_qty = qty
    product.save(update_fields=['stock_qty'])

    return Response({
        'success': True,
        'product': ProductSerializer(product).data,
        'movement': {
            'id': None,
            'product_id': product.id,
            'movement_type': movement_type,
            'quantity': qty,
            'note': request.data.get('note', ''),
            'reference': request.data.get('reference', ''),
        },
    })


class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticated]
