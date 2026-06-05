# products/management/commands/update_suggestions.py
from django.core.management.base import BaseCommand
from products.suggestion_engine import update_all_suggestions

class Command(BaseCommand):
    help = 'Update stock suggestions for all active products'

    def handle(self, *args, **options):
        count = update_all_suggestions()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated suggestions for {count} products.')
        )