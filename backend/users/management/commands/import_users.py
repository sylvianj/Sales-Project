# users/management/commands/import_users.py
import pandas as pd
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import Role, UserRole

class Command(BaseCommand):
    help = 'Import users from Excel file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)

    def handle(self, *args, **options):
        df = pd.read_excel(options['file_path'])
        for _, row in df.iterrows():
            user, created = User.objects.update_or_create(
                username=row['username'],
                defaults={
                    'email': row['email'],
                    'first_name': row.get('first_name', ''),
                    'last_name': row.get('last_name', ''),
                }
            )
            if created or 'password' in row:
                user.set_password(row['password'])
                user.save()

            role_name = row.get('role')
            if role_name:
                role, _ = Role.objects.get_or_create(name=role_name)
                UserRole.objects.get_or_create(user=user, role=role)

            self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Updated"}: {user.username}'))