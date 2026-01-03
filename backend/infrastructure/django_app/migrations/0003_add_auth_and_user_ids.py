"""
Add authentication support and user association to carts and orders.

This migration:
1. Deletes existing cart and order data (as per migration strategy)
2. Creates UserProfile model
3. Adds user_id to CartModel and OrderModel
4. Creates a default admin user
"""

import uuid

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations, models


def delete_existing_data(apps, schema_editor):
    """Delete existing carts and orders before adding user_id."""
    CartItemModel = apps.get_model("django_app", "CartItemModel")
    CartModel = apps.get_model("django_app", "CartModel")
    OrderItemModel = apps.get_model("django_app", "OrderItemModel")
    OrderModel = apps.get_model("django_app", "OrderModel")

    CartItemModel.objects.all().delete()
    CartModel.objects.all().delete()
    OrderItemModel.objects.all().delete()
    OrderModel.objects.all().delete()


def create_default_admin(apps, schema_editor):
    """Create a default admin user."""
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("django_app", "UserProfile")

    # Create admin user if it doesn't exist
    admin_user, created = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@example.com",
            "password": make_password("admin"),
            "is_staff": True,
            "is_superuser": True,
        },
    )

    # Create profile for admin
    UserProfile.objects.get_or_create(
        user=admin_user,
        defaults={
            "id": uuid.uuid4(),
            "role": "admin",
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("django_app", "0002_auditlogmodel"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Step 1: Delete existing cart and order data
        migrations.RunPython(delete_existing_data, migrations.RunPython.noop),
        # Step 2: Create UserProfile model
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[("admin", "Admin"), ("customer", "Customer")],
                        default="customer",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "user_profile",
            },
        ),
        # Step 3: Add user_id to CartModel
        migrations.AddField(
            model_name="cartmodel",
            name="user_id",
            field=models.UUIDField(db_index=True, default=uuid.uuid4),
            preserve_default=False,
        ),
        # Step 4: Add unique constraint on cart user_id
        migrations.AddConstraint(
            model_name="cartmodel",
            constraint=models.UniqueConstraint(
                fields=("user_id",), name="unique_cart_per_user"
            ),
        ),
        # Step 5: Add user_id to OrderModel
        migrations.AddField(
            model_name="ordermodel",
            name="user_id",
            field=models.UUIDField(db_index=True, default=uuid.uuid4),
            preserve_default=False,
        ),
        # Step 6: Create default admin user
        migrations.RunPython(create_default_admin, migrations.RunPython.noop),
    ]
