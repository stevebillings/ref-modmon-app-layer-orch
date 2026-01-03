"""
Django management command to seed the database with test products.

Usage:
    python manage.py seed_products           # Creates 50 products (default)
    python manage.py seed_products --count 100
    python manage.py seed_products --clear   # Clear existing products first
"""
import random
from decimal import Decimal

from django.core.management.base import BaseCommand

from infrastructure.django_app.models import ProductModel


class Command(BaseCommand):
    help = "Seed the database with test products for pagination testing"

    # Product name components for generating varied product names
    ADJECTIVES = [
        "Premium", "Classic", "Deluxe", "Essential", "Professional",
        "Ultra", "Compact", "Portable", "Advanced", "Smart",
        "Organic", "Natural", "Handcrafted", "Vintage", "Modern",
        "Eco-Friendly", "Wireless", "Digital", "High-Performance", "Budget",
    ]

    CATEGORIES = [
        "Laptop", "Keyboard", "Mouse", "Monitor", "Headphones",
        "Speaker", "Camera", "Tablet", "Phone", "Watch",
        "Charger", "Cable", "Adapter", "Stand", "Case",
        "Bag", "Light", "Microphone", "Webcam", "Hub",
        "Printer", "Scanner", "Drive", "Router", "Switch",
    ]

    VARIANTS = [
        "Pro", "Plus", "Max", "Mini", "Lite",
        "X", "S", "SE", "Elite", "Air",
        "2024", "Gen 2", "Gen 3", "MK II", "Rev B",
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=50,
            help="Number of products to create (default: 50)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing products before seeding",
        )

    def handle(self, *args, **options):
        count = options["count"]
        clear = options["clear"]

        if clear:
            deleted_count, _ = ProductModel.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f"Deleted {deleted_count} existing products")
            )

        created_count = 0
        skipped_count = 0
        used_names = set(ProductModel.objects.values_list("name", flat=True))

        for _ in range(count):
            name = self._generate_unique_name(used_names)
            if name is None:
                self.stdout.write(
                    self.style.WARNING(
                        "Could not generate more unique names. Stopping."
                    )
                )
                break

            used_names.add(name)

            # Generate price between $9.99 and $999.99
            price = Decimal(random.randint(999, 99999)) / 100

            # Generate stock between 0 and 500
            stock = random.randint(0, 500)

            try:
                ProductModel.objects.create(
                    name=name,
                    price=price,
                    stock_quantity=stock,
                )
                created_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to create '{name}': {e}")
                )
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_count} products"
                + (f" (skipped {skipped_count})" if skipped_count else "")
            )
        )

    def _generate_unique_name(self, used_names: set, max_attempts: int = 100) -> str | None:
        """Generate a unique product name not already in used_names."""
        for _ in range(max_attempts):
            adj = random.choice(self.ADJECTIVES)
            cat = random.choice(self.CATEGORIES)
            var = random.choice(self.VARIANTS)

            # Randomly include or exclude variant
            if random.random() > 0.3:
                name = f"{adj} {cat} {var}"
            else:
                name = f"{adj} {cat}"

            if name not in used_names:
                return name

        return None
