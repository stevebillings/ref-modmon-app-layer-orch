import uuid

from django.db import models


class ProductModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product"
        ordering = ["name"]

    def __str__(self):
        return self.name


class CartModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cart"

    def __str__(self):
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

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


class OrderModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order"
        ordering = ["-submitted_at"]

    def __str__(self):
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

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
