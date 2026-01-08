"""
Django management command to reset the test database for E2E testing.

Usage:
    python manage.py reset_test_db

This command:
1. Flushes all data from the database
2. Seeds test users (admin, customer)
3. Optionally seeds initial products
"""
from typing import Any

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand

from infrastructure.django_app.models import (
    CartItemModel,
    CartModel,
    OrderItemModel,
    OrderModel,
    ProductModel,
    UserProfile,
)


class Command(BaseCommand):
    help = "Reset the database for E2E testing - clears all data and seeds test users"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--seed-products",
            action="store_true",
            help="Also seed initial products",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write("Resetting test database...")

        # Clear all application data in correct order (respecting foreign keys)
        self.stdout.write("  Clearing order items...")
        OrderItemModel.objects.all().delete()

        self.stdout.write("  Clearing orders...")
        OrderModel.objects.all().delete()

        self.stdout.write("  Clearing cart items...")
        CartItemModel.objects.all().delete()

        self.stdout.write("  Clearing carts...")
        CartModel.objects.all().delete()

        self.stdout.write("  Clearing products...")
        ProductModel.objects.all().delete()

        self.stdout.write("  Clearing user profiles...")
        UserProfile.objects.all().delete()

        self.stdout.write("  Clearing users (except superusers)...")
        User.objects.filter(is_superuser=False).delete()

        # Seed test users
        self.stdout.write("  Creating test users...")
        self._create_test_users()

        # Optionally seed products
        if options.get("seed_products"):
            self.stdout.write("  Seeding products...")
            call_command("seed_products", verbosity=0)

        self.stdout.write(self.style.SUCCESS("Database reset complete!"))

    def _create_test_users(self) -> None:
        """Create test users for E2E testing."""
        test_users = [
            {"username": "admin", "password": "admin", "role": "admin"},
            {"username": "customer", "password": "customer", "role": "customer"},
            {"username": "alice", "password": "alice", "role": "customer"},
            {"username": "bob", "password": "bob", "role": "customer"},
            # Dedicated user for "no orders" test - never used by other tests
            {"username": "noorders", "password": "noorders", "role": "customer"},
        ]

        for user_data in test_users:
            username = user_data["username"]
            password = user_data["password"]
            role = user_data["role"]

            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@test.com"},
            )

            user.set_password(password)
            user.save()

            UserProfile.objects.update_or_create(
                user=user,
                defaults={"role": role},
            )

            status = "Created" if created else "Updated"
            self.stdout.write(f"    {status} user '{username}' with role '{role}'")
