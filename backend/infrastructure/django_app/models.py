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
    shipping_address = models.JSONField(default=dict)
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


class FeatureFlagModel(models.Model):
    """
    Feature flag for toggling features on/off.

    Simple on/off toggles stored in the database.
    Unknown flags default to disabled (False).
    Flags can target specific user groups for granular rollouts.
    """

    name = models.CharField(max_length=100, unique=True)
    enabled = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "feature_flag"
        ordering = ["name"]

    def __str__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"{self.name} ({status})"


class UserGroupModel(models.Model):
    """
    User group for feature flag targeting.

    Groups are separate from roles - roles are for authorization (what you can do),
    while groups are for targeting (which features you see).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_group"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class UserGroupMembershipModel(models.Model):
    """
    Many-to-many relationship between users and groups.

    A user can belong to multiple groups for feature flag targeting.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="group_memberships",
    )
    group = models.ForeignKey(
        UserGroupModel,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_group_membership"
        constraints = [
            models.UniqueConstraint(
                fields=["user_profile", "group"],
                name="unique_user_group_membership",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user_profile} in {self.group}"


class FeatureFlagTargetModel(models.Model):
    """
    Many-to-many relationship between feature flags and target groups.

    When a flag has target groups, it is only enabled for users in those groups.
    When a flag has no target groups, it is enabled for everyone (if enabled=True).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feature_flag = models.ForeignKey(
        FeatureFlagModel,
        on_delete=models.CASCADE,
        related_name="target_groups",
    )
    group = models.ForeignKey(
        UserGroupModel,
        on_delete=models.CASCADE,
        related_name="targeted_flags",
    )

    class Meta:
        db_table = "feature_flag_target"
        constraints = [
            models.UniqueConstraint(
                fields=["feature_flag", "group"],
                name="unique_flag_target",
            )
        ]

    def __str__(self) -> str:
        return f"{self.feature_flag.name} -> {self.group.name}"
