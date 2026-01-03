from decimal import Decimal, InvalidOperation

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
    PermissionDeniedError,
    ProductAlreadyDeletedError,
    ProductInUseError,
    ProductNotDeletedError,
    ProductNotFoundError,
    ValidationError,
)
from domain.user_context import UserContext
from infrastructure.django_app.auth_decorators import require_auth
from infrastructure.django_app.user_context_adapter import build_user_context
from infrastructure.django_app.serialization import to_dict
from infrastructure.django_app.unit_of_work import unit_of_work
from infrastructure.events import get_event_dispatcher


def handle_domain_error(error: DomainError) -> Response:
    """Convert domain errors to appropriate HTTP responses."""
    if isinstance(error, PermissionDeniedError):
        return Response(
            {"error": str(error)},
            status=status.HTTP_403_FORBIDDEN,
        )
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
    if isinstance(error, ProductAlreadyDeletedError):
        return Response(
            {"error": str(error)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if isinstance(error, ProductNotDeletedError):
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


def _get_optional_user_context(request: Request) -> UserContext | None:
    """Get user context if authenticated, None otherwise."""
    if hasattr(request, "user") and request.user.is_authenticated:
        try:
            return build_user_context(request.user)
        except Exception:
            return None
    return None


def _parse_int(value: str | None, default: int) -> int:
    """Safely parse an integer from a query parameter."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _parse_decimal(value: str | None) -> Decimal | None:
    """Safely parse a decimal from a query parameter."""
    if value is None:
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _parse_bool(value: str | None) -> bool | None:
    """Safely parse a boolean from a query parameter."""
    if value is None:
        return None
    return value.lower() in ("true", "1", "yes")


@api_view(["GET"])
def products_list(request: Request) -> Response:
    """
    List products with optional pagination and filtering. Public endpoint.

    Query parameters:
        page: Page number (1-indexed, default 1)
        page_size: Items per page (default 20, max 100)
        search: Search term for product name
        min_price: Minimum price filter
        max_price: Maximum price filter
        in_stock: If "true", only return products with stock > 0
        include_deleted: If "true" and user is admin, include soft-deleted products
    """
    with unit_of_work(get_event_dispatcher()) as uow:
        service = ProductService(uow)

        # Parse query parameters
        page = _parse_int(request.query_params.get("page"), 1)
        page_size = _parse_int(request.query_params.get("page_size"), 20)
        search = request.query_params.get("search") or None
        min_price = _parse_decimal(request.query_params.get("min_price"))
        max_price = _parse_decimal(request.query_params.get("max_price"))
        in_stock = _parse_bool(request.query_params.get("in_stock"))
        include_deleted = _parse_bool(request.query_params.get("include_deleted"))

        # Get user context if authenticated (for include_deleted check)
        user_context = _get_optional_user_context(request)

        result = service.get_products_paginated(
            page=page,
            page_size=page_size,
            search=search,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock,
            include_deleted=include_deleted or False,
            user_context=user_context,
        )

        return Response({
            "results": [to_dict(p) for p in result.items],
            "page": result.page,
            "page_size": result.page_size,
            "total_count": result.total_count,
            "total_pages": result.total_pages,
            "has_next": result.has_next,
            "has_previous": result.has_previous,
        })


@api_view(["POST"])
@require_auth
def product_create(request: Request, user_context: UserContext) -> Response:
    """Create a new product. Admin only."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = ProductService(uow)
        try:
            data = request.data
            product = service.create_product(
                name=data.get("name", ""),
                price=data.get("price", "0"),
                stock_quantity=int(data.get("stock_quantity", 0)),
                user_context=user_context,
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
@require_auth
def product_delete(request: Request, product_id: str, user_context: UserContext) -> Response:
    """Soft-delete a product. Admin only."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = ProductService(uow)
        try:
            service.delete_product(product_id, user_context=user_context)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DomainError as e:
            return handle_domain_error(e)


@api_view(["POST"])
@require_auth
def product_restore(request: Request, product_id: str, user_context: UserContext) -> Response:
    """Restore a soft-deleted product. Admin only."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = ProductService(uow)
        try:
            product = service.restore_product(product_id, user_context=user_context)
            return Response(to_dict(product), status=status.HTTP_200_OK)
        except DomainError as e:
            return handle_domain_error(e)


# --- Cart Endpoints ---


@api_view(["GET"])
@require_auth
def cart_get(request: Request, user_context: UserContext) -> Response:
    """Get the current user's cart."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = CartService(uow)
        cart = service.get_cart(user_context=user_context)
        cart_dict = to_dict(cart)
        cart_dict["total"] = str(cart.get_total())
        cart_dict["item_count"] = cart.get_item_count()
        return Response(cart_dict)


@api_view(["POST"])
@require_auth
def cart_add_item(request: Request, user_context: UserContext) -> Response:
    """Add an item to the user's cart."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = CartService(uow)
        try:
            data = request.data
            cart = service.add_item(
                product_id=data.get("product_id", ""),
                quantity=int(data.get("quantity", 0)),
                user_context=user_context,
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
@require_auth
def cart_update_item(request: Request, product_id: str, user_context: UserContext) -> Response:
    """Update the quantity of an item in the user's cart."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = CartService(uow)
        try:
            data = request.data
            cart = service.update_item_quantity(
                product_id=product_id,
                quantity=int(data.get("quantity", 0)),
                user_context=user_context,
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
@require_auth
def cart_remove_item(request: Request, product_id: str, user_context: UserContext) -> Response:
    """Remove an item from the user's cart."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = CartService(uow)
        try:
            cart = service.remove_item(product_id=product_id, user_context=user_context)
            cart_dict = to_dict(cart)
            cart_dict["total"] = str(cart.get_total())
            cart_dict["item_count"] = cart.get_item_count()
            return Response(cart_dict)
        except DomainError as e:
            return handle_domain_error(e)


@api_view(["POST"])
@require_auth
def cart_submit(request: Request, user_context: UserContext) -> Response:
    """Submit the user's cart as an order."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = CartService(uow)
        try:
            order = service.submit_cart(user_context=user_context)
            order_dict = to_dict(order)
            order_dict["total"] = str(order.get_total())
            return Response(order_dict, status=status.HTTP_201_CREATED)
        except DomainError as e:
            return handle_domain_error(e)


# --- Order Endpoints ---


@api_view(["GET"])
@require_auth
def orders_list(request: Request, user_context: UserContext) -> Response:
    """List orders. Admins see all; customers see only their own."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = OrderService(uow)
        orders = service.get_orders(user_context=user_context)
        results = []
        for order in orders:
            order_dict = to_dict(order)
            order_dict["total"] = str(order.get_total())
            results.append(order_dict)
        return Response({"results": results})
