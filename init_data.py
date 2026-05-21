# init_data.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_sales.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import Role, UserRole
from products.models import Product
from customers.models import Customer

print("=" * 50)
print("ADDING SAMPLE DATA")
print("=" * 50)

# 1. Create Roles
roles = [
    ('cashier', 'Can process sales and returns'),
    ('accountant', 'Can view reports and transactions'),
    ('administrator', 'Full system access'),
]

for name, desc in roles:
    role, created = Role.objects.get_or_create(name=name, defaults={'description': desc})
    print(f"{'✅ Created' if created else '⏭️ Exists'}: {name}")

# 2. Create Sample Products
products = [
    {'sku': 'P001', 'name': 'Laptop Pro', 'price': 50000, 'stock_qty': 10},
    {'sku': 'P002', 'name': 'Wireless Mouse', 'price': 1500, 'stock_qty': 50},
    {'sku': 'P003', 'name': 'Mechanical Keyboard', 'price': 3000, 'stock_qty': 30},
    {'sku': 'P004', 'name': '24" Monitor', 'price': 15000, 'stock_qty': 15},
    {'sku': 'P005', 'name': 'USB-C Cable', 'price': 500, 'stock_qty': 100},
]

for p in products:
    product, created = Product.objects.get_or_create(
        sku=p['sku'],
        defaults={
            'name': p['name'],
            'price': p['price'],
            'stock_qty': p['stock_qty'],
            'tax_rate': 16.00,
        }
    )
    print(f"{'✅ Created' if created else '⏭️ Exists'}: {p['sku']} - {p['name']}")

# 3. Create Sample Customer
customer, created = Customer.objects.get_or_create(
    name='John Doe',
    defaults={
        'phone': '0712345678',
        'email': 'john@example.com',
        'address': 'Nairobi, Kenya',
    }
)
print(f"{'✅ Created' if created else '⏭️ Exists'}: Customer - John Doe")

# 4. Create Cashier User
cashier, created = User.objects.get_or_create(
    username='cashier1',
    defaults={
        'email': 'cashier@system.com',
        'first_name': 'Jane',
        'last_name': 'Cashier',
    }
)
if created:
    cashier.set_password('cashier123')
    cashier.save()
    print(f"✅ Created: cashier1 / cashier123")
    
    # Assign cashier role
    cashier_role = Role.objects.get(name='cashier')
    UserRole.objects.get_or_create(user=cashier, role=cashier_role)
    print(f"✅ Assigned cashier role")

print("\n" + "=" * 50)
print("✅ SAMPLE DATA ADDED SUCCESSFULLY!")
print("=" * 50)
print("\n📝 LOGIN CREDENTIALS:")
print("   Admin:    admin / (your password)")
print("   Cashier:  cashier1 / cashier123")
print("\n🌐 Admin Panel: http://127.0.0.1:8000/admin/")