"""
Management command to create stock categories
Run: python manage.py create_stock_categories
"""
from django.core.management.base import BaseCommand
from stock_tracker.models import StockCategory


class Command(BaseCommand):
    help = 'Create stock categories (D, B, S, W, M)'

    def handle(self, *args, **options):
        categories = [
            ('D', 'Draught Beer'),
            ('B', 'Bottled Beer'),
            ('S', 'Spirits'),
            ('W', 'Wine'),
            ('M', 'Minerals & Syrups'),
        ]

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("CREATING STOCK CATEGORIES")
        self.stdout.write("=" * 60 + "\n")

        for code, name in categories:
            category, created = StockCategory.objects.get_or_create(
                code=code,
                defaults={'name': name}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Created: {code} - {name}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"• Already exists: {code} - {name}")
                )

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS("✅ Stock categories setup complete!")
        )
        self.stdout.write("=" * 60 + "\n")

        # Display all categories
        all_categories = StockCategory.objects.all().order_by('code')
        self.stdout.write("\nCurrent categories:")
        for cat in all_categories:
            self.stdout.write(f"  {cat.code} - {cat.name}")
