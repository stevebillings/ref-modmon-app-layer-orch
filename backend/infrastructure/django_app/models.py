import uuid

from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """
    Extends Django User with application-specific fields.

    Uses OneToOne relationship to keep auth separate from application concerns.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(
        max_length=20,
        choices=[("admin", "Admin"), ("customer", "Customer")],
        default="customer",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_profile"

    def __str__(self) -> str:
        return f"{self.user.username} ({self.role})"


class ProductModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "product"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class CartModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cart"
        constraints = [
            models.UniqueConstraint(fields=["user_id"], name="unique_cart_per_user")
        ]

    def __str__(self) -> str:
        return f"Cart {self.id}"


class CartItemModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(
        CartModel, on_delete=models.CASCADE, related_name="items"
    )
    # product_id stored as UUID (not FK) to maintain aggregate isolation
    product_id = models.UUIDField()
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    class Meta:
        db_table = "cart_item"
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product_id"], name="unique_product_per_cart"
            )
        ]

    def __str__(self) -> str:
        return f"{self.product_name} x {self.quantity}"


class OrderModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order"
        ordering = ["-submitted_at"]

    def __str__(self) -> str:
        return f"Order {self.id}"


class OrderItemModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        OrderModel, on_delete=models.CASCADE, related_name="items"
    )
    product_id = models.UUIDField()
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    class Meta:
        db_table = "order_item"

    def __str__(self) -> str:
        return f"{self.product_name} x {self.quantity}"


class AuditLogModel(models.Model):
    """
    Audit log for tracking domain events.

    Stores all domain events as an immutable audit trail.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=100, db_index=True)
    event_id = models.UUIDField()
    occurred_at = models.DateTimeField(db_index=True)
    actor_id = models.CharField(max_length=100, db_index=True)
    aggregate_type = models.CharField(max_length=100)
    aggregate_id = models.UUIDField(db_index=True)
    event_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["aggregate_type", "aggregate_id"]),
            models.Index(fields=["actor_id", "occurred_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} at {self.occurred_at}"
