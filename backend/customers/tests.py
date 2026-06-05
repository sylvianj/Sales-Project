import os
import tempfile
import pandas as pd
from django.core.management import call_command
from django.test import TestCase
from .models import Customer


class CustomerImportCommandTest(TestCase):
    def test_import_customers_from_excel(self):
        records = [
            {'name': 'Test Customer', 'phone': '0712345678', 'email': 'test@example.com', 'address': '123 Test St', 'loyalty_points': 10},
            {'name': 'Another Customer', 'phone': '0723456789', 'email': 'another@example.com', 'address': '456 Sample Rd', 'loyalty_points': 5},
        ]
        df = pd.DataFrame(records)

        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        temp_file.close()
        file_path = temp_file.name
        df.to_excel(file_path, index=False)

        try:
            call_command('import_customers', file_path)
            self.assertEqual(Customer.objects.count(), 2)
            self.assertTrue(Customer.objects.filter(name='Test Customer').exists())
            self.assertTrue(Customer.objects.filter(name='Another Customer').exists())
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
