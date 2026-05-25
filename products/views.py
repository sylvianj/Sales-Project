# products/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import F  # ← ADD THIS IMPORT
from .models import Product
from .serializers import ProductSerializer
from .suggestion_engine import generate_suggestion, update_all_suggestions
from users.permissions import IsStoreKeeper

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsStoreKeeper])
    def suggestion(self, request, pk=None):
        product = self.get_object()
        data = generate_suggestion(product)
        return Response(data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsStoreKeeper])
    def all_suggestions(self, request):
        update_all_suggestions()
        products = Product.objects.filter(is_active=True).values(
            'id', 'name', 'sku', 'stock_qty', 'reorder_level',
            'suggested_order_quantity', 'suggestion_reason', 'last_suggestion_generated'
        )
        return Response(list(products))

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsStoreKeeper])
    def update_notes(self, request, pk=None):
        product = self.get_object()
        notes = request.data.get('notes', '')
        product.store_keeper_notes = notes
        product.save(update_fields=['store_keeper_notes'])
        return Response({'message': 'Notes updated', 'notes': notes})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsStoreKeeper])
    def low_stock(self, request):
        # Use F from django.db.models – now imported
        low = Product.objects.filter(stock_qty__lte=F('reorder_level'), is_active=True)
        serializer = self.get_serializer(low, many=True)
        return Response(serializer.data)# products/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import F  # ← ADD THIS IMPORT
from .models import Product
from .serializers import ProductSerializer
from .suggestion_engine import generate_suggestion, update_all_suggestions
from users.permissions import IsStoreKeeper

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsStoreKeeper])
    def suggestion(self, request, pk=None):
        product = self.get_object()
        data = generate_suggestion(product)
        return Response(data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsStoreKeeper])
    def all_suggestions(self, request):
        update_all_suggestions()
        products = Product.objects.filter(is_active=True).values(
            'id', 'name', 'sku', 'stock_qty', 'reorder_level',
            'suggested_order_quantity', 'suggestion_reason', 'last_suggestion_generated'
        )
        return Response(list(products))

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsStoreKeeper])
    def update_notes(self, request, pk=None):
        product = self.get_object()
        notes = request.data.get('notes', '')
        product.store_keeper_notes = notes
        product.save(update_fields=['store_keeper_notes'])
        return Response({'message': 'Notes updated', 'notes': notes})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsStoreKeeper])
    def low_stock(self, request):
        # Use F from django.db.models – now imported
        low = Product.objects.filter(stock_qty__lte=F('reorder_level'), is_active=True)
        serializer = self.get_serializer(low, many=True)
        return Response(serializer.data)