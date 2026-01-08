"""
Django management command to seed the database with test users.

Usage:
    python manage.py seed_test_users
"""
from typing import Any

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from infrastructure.django_app.models import UserProfile


class Command(BaseCommand):
    help = "Seed the database with test users for E2E testing"

    TEST_USERS = [
        {"username": "admin", "password": "admin", "role": "admin"},
        {"username": "customer", "password": "customer", "role": "customer"},
    ]

    def handle(self, *args: Any, **options: Any) -> None:
        for user_data in self.TEST_USERS:
            username = user_data["username"]
            password = user_data["password"]
            role = user_data["role"]

            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@test.com"},
            )

            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Created user '{username}'")
                )
            else:
                # Ensure password is correct
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.WARNING(f"User '{username}' already exists, updated password")
                )

            # Update or create profile with correct role
            profile, _ = UserProfile.objects.get_or_create(user=user)
            if profile.role != role:
                profile.role = role
                profile.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Updated '{username}' role to '{role}'")
                )

        self.stdout.write(
            self.style.SUCCESS("Test users seeded successfully")
        )
