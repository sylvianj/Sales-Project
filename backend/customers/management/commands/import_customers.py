# customers/management/commands/import_customers.py
import pandas as pd
from django.core.management.base import BaseCommand
from customers.models import Customer

class Command(BaseCommand):   # ← Class name must be "Command"
    help = 'Import customers from Excel file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to Excel file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        df = pd.read_excel(file_path)

        for _, row in df.iterrows():
            obj, created = Customer.objects.update_or_create(
                name=row['name'],
                defaults={
                    'phone': row.get('phone'),
                    'email': row.get('email'),
                    'address': row.get('address'),
                    'loyalty_points': row.get('loyalty_points', 0),
                }
            )
            self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Updated"}: {obj.name}'))