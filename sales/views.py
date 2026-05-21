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
        """Create a new sale with items"""
        data = request.data
        
        # Get or create customer
        customer_id = data.get('customer_id')
        customer = None
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
            except Customer.DoesNotExist:
                return Response({'error': 'Customer not found'}, status=404)
        
        # Calculate totals
        subtotal = 0
        items_data = []
        
        for item in data.get('items', []):
            try:
                product = Product.objects.get(id=item['product_id'])
            except Product.DoesNotExist:
                return Response({'error': f"Product {item['product_id']} not found"}, status=404)
            
            if product.stock_qty < item['quantity']:
                return Response({'error': f"Insufficient stock for {product.name}"}, status=400)
            
            item_total = float(product.price) * item['quantity']
            subtotal += item_total
            
            items_data.append({
                'product': product,
                'quantity': item['quantity'],
                'unit_price': product.price,
                'discount': item.get('discount', 0),
                'total': item_total
            })
        
        # Apply discount (16% tax)
        discount = float(data.get('discount', 0))
        tax_rate = 16
        after_discount = subtotal - discount
        tax_amount = after_discount * (tax_rate / 100)
        grand_total = after_discount + tax_amount
        
        # Calculate change
        paid_amount = float(data.get('paid_amount', 0))
        change_due = paid_amount - grand_total
        
        if change_due < 0:
            return Response({'error': f'Insufficient payment. Required: {grand_total}'}, status=400)
        
        # Create sale
        sale = Sale.objects.create(
            customer=customer,
            cashier=request.user,
            subtotal=subtotal,
            discount=discount,
            tax_amount=tax_amount,
            total=grand_total,
            paid_amount=paid_amount,
            change_due=change_due,
            payment_method=data.get('payment_method', 'cash'),
            status='completed'
        )
        
        # Create sale items and update stock
        for item_data in items_data:
            SaleItem.objects.create(
                sale=sale,
                product=item_data['product'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                discount=item_data['discount'],
                total=item_data['total']
            )
            item_data['product'].stock_qty -= item_data['quantity']
            item_data['product'].save()
        
        # Prepare receipt
        receipt = {
            'sale_no': sale.sale_no,
            'date': sale.sale_date.strftime('%Y-%m-%d %H:%M:%S'),
            'cashier': sale.cashier.username,
            'customer': sale.customer.name if sale.customer else 'Walk-in Customer',
            'items': [
                {
                    'name': item['product'].name,
                    'quantity': item['quantity'],
                    'unit_price': float(item['unit_price']),
                    'total': float(item['total'])
                }
                for item in items_data
            ],
            'subtotal': float(subtotal),
            'discount': float(discount),
            'tax': float(tax_amount),
            'total': float(grand_total),
            'paid': float(paid_amount),
            'change': float(change_due)
        }
        
        return Response({
            'sale_id': sale.id,
            'sale_no': sale.sale_no,
            'receipt': receipt
        }, status=status.HTTP_201_CREATED)

        # Add to your existing SaleViewSet in sales/views.py

@action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
def daily_summary(self, request):
    """Get daily sales summary (Accountant only)"""
    from datetime import datetime, timedelta
    
    date_str = request.query_params.get('date', datetime.now().strftime('%Y-%m-%d'))
    date = datetime.strptime(date_str, '%Y-%m-%d')
    
    sales = Sale.objects.filter(
        sale_date__date=date,
        status='completed'
    )
    
    total_sales = sales.count()
    total_revenue = sum(float(s.total) for s in sales)
    total_tax = sum(float(s.tax_amount) for s in sales)
    total_discount = sum(float(s.discount) for s in sales)
    
    return Response({
        'date': date_str,
        'total_sales': total_sales,
        'total_revenue': round(total_revenue, 2),
        'total_tax': round(total_tax, 2),
        'total_discount': round(total_discount, 2),
        'average_sale': round(total_revenue / total_sales if total_sales > 0 else 0, 2)
    })

@action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
def transaction_history(self, request):
    """Get transaction history (Accountant only)"""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    queryset = Sale.objects.filter(status='completed')
    
    if start_date:
        queryset = queryset.filter(sale_date__date__gte=start_date)
    if end_date:
        queryset = queryset.filter(sale_date__date__lte=end_date)
    
    queryset = queryset.order_by('-sale_date')[:100]
    
    return Response([
        {
            'sale_no': s.sale_no,
            'date': s.sale_date.strftime('%Y-%m-%d %H:%M'),
            'customer': s.customer.name if s.customer else 'Walk-in',
            'cashier': s.cashier.username,
            'total': float(s.total),
            'status': s.status
        }
        for s in queryset
    ])
@action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
def dashboard_stats(self, request):
    """Get dashboard statistics (Admin only)"""
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    # Today's sales
    today_sales = Sale.objects.filter(sale_date__date=today, status='completed')
    today_revenue = sum(float(s.total) for s in today_sales)
    
    # Week's sales
    week_sales = Sale.objects.filter(sale_date__date__gte=week_ago, status='completed')
    week_revenue = sum(float(s.total) for s in week_sales)
    
    # Low stock products
    low_stock = Product.objects.filter(stock_qty__lte=5, is_active=True).count()
    
    # Total customers
    total_customers = Customer.objects.count()
    
    # Recent sales
    recent_sales = Sale.objects.order_by('-sale_date')[:5]
    
    return Response({
        'today': {
            'sales_count': today_sales.count(),
            'revenue': round(today_revenue, 2)
        },
        'this_week': {
            'sales_count': week_sales.count(),
            'revenue': round(week_revenue, 2)
        },
        'alerts': {
            'low_stock_products': low_stock
        },
        'total_customers': total_customers,
        'recent_sales': [
            {
                'sale_no': s.sale_no,
                'date': s.sale_date.strftime('%Y-%m-%d %H:%M'),
                'total': float(s.total)
            }
            for s in recent_sales
        ]
    })