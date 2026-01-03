from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from application.services.cart_service import CartService
from application.services.order_service import OrderService
from application.services.product_service import ProductService
from domain.exceptions import (
    CartItemNotFoundError,
    DomainError,
    DuplicateProductError,
    EmptyCartError,
    InsufficientStockError,
    ProductInUseError,
    ProductNotFoundError,
    ValidationError,
)
from infrastructure.django_app.serialization import to_dict
from infrastructure.django_app.unit_of_work import unit_of_work
from infrastructure.events import get_event_dispatcher


def handle_domain_error(error: DomainError) -> Response:
    """Convert domain errors to appropriate HTTP responses."""
    if isinstance(error, ValidationError):
        return Response(
            {"error": error.message, "field": error.field},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if isinstance(error, DuplicateProductError):
        return Response(
            {"error": str(error)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if isinstance(error, ProductNotFoundError):
        return Response(
            {"error": str(error)},
            status=status.HTTP_404_NOT_FOUND,
        )
    if isinstance(error, ProductInUseError):
        return Response(
            {"error": str(error)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if isinstance(error, InsufficientStockError):
        return Response(
            {"error": str(error)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if isinstance(error, CartItemNotFoundError):
        return Response(
            {"error": str(error)},
            status=status.HTTP_404_NOT_FOUND,
        )
    if isinstance(error, EmptyCartError):
        return Response(
            {"error": str(error)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    # Generic domain error
    return Response(
        {"error": str(error)},
        status=status.HTTP_400_BAD_REQUEST,
    )


# --- Product Endpoints ---


@api_view(["GET", "POST"])
def products_list_create(request: Request) -> Response:
    """List all products or create a new product."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = ProductService(uow)

        if request.method == "GET":
            products = service.get_all_products()
            return Response({"results": [to_dict(p) for p in products]})

        # POST - create product
        try:
            data = request.data
            product = service.create_product(
                name=data.get("name", ""),
                price=data.get("price", "0"),
                stock_quantity=int(data.get("stock_quantity", 0)),
            )
            return Response(to_dict(product), status=status.HTTP_201_CREATED)
        except DomainError as e:
            return handle_domain_error(e)
        except (ValueError, TypeError) as e:
            return Response(
                {"error": f"Invalid input: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


@api_view(["DELETE"])
def product_delete(request: Request, product_id: str) -> Response:
    """Delete a product."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = ProductService(uow)
        try:
            service.delete_product(product_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DomainError as e:
            return handle_domain_error(e)


# --- Cart Endpoints ---


@api_view(["GET"])
def cart_get(request: Request) -> Response:
    """Get the current cart."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = CartService(uow)
        cart = service.get_cart()
        cart_dict = to_dict(cart)
        cart_dict["total"] = str(cart.get_total())
        cart_dict["item_count"] = cart.get_item_count()
        return Response(cart_dict)


@api_view(["POST"])
def cart_add_item(request: Request) -> Response:
    """Add an item to the cart."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = CartService(uow)
        try:
            data = request.data
            cart = service.add_item(
                product_id=data.get("product_id", ""),
                quantity=int(data.get("quantity", 0)),
            )
            cart_dict = to_dict(cart)
            cart_dict["total"] = str(cart.get_total())
            cart_dict["item_count"] = cart.get_item_count()
            return Response(cart_dict)
        except DomainError as e:
            return handle_domain_error(e)
        except (ValueError, TypeError) as e:
            return Response(
                {"error": f"Invalid input: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


@api_view(["PATCH"])
def cart_update_item(request: Request, product_id: str) -> Response:
    """Update the quantity of an item in the cart."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = CartService(uow)
        try:
            data = request.data
            cart = service.update_item_quantity(
                product_id=product_id,
                quantity=int(data.get("quantity", 0)),
            )
            cart_dict = to_dict(cart)
            cart_dict["total"] = str(cart.get_total())
            cart_dict["item_count"] = cart.get_item_count()
            return Response(cart_dict)
        except DomainError as e:
            return handle_domain_error(e)
        except (ValueError, TypeError) as e:
            return Response(
                {"error": f"Invalid input: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


@api_view(["DELETE"])
def cart_remove_item(request: Request, product_id: str) -> Response:
    """Remove an item from the cart."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = CartService(uow)
        try:
            cart = service.remove_item(product_id=product_id)
            cart_dict = to_dict(cart)
            cart_dict["total"] = str(cart.get_total())
            cart_dict["item_count"] = cart.get_item_count()
            return Response(cart_dict)
        except DomainError as e:
            return handle_domain_error(e)


@api_view(["POST"])
def cart_submit(request: Request) -> Response:
    """Submit the cart as an order."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = CartService(uow)
        try:
            order = service.submit_cart()
            order_dict = to_dict(order)
            order_dict["total"] = str(order.get_total())
            return Response(order_dict, status=status.HTTP_201_CREATED)
        except DomainError as e:
            return handle_domain_error(e)


# --- Order Endpoints ---


@api_view(["GET"])
def orders_list(request: Request) -> Response:
    """List all orders."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = OrderService(uow)
        orders = service.get_all_orders()
        results = []
        for order in orders:
            order_dict = to_dict(order)
            order_dict["total"] = str(order.get_total())
            results.append(order_dict)
        return Response({"results": results})
