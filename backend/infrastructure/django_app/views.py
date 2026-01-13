from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from application.ports.feature_flag_repository import FeatureFlag
from application.queries.product_report import ProductReportQuery
from application.services.cart_service import CartService
from application.services.feature_flag_service import (
    DuplicateFeatureFlagError,
    FeatureFlagNotFoundError,
    FeatureFlagService,
)
from application.services.user_group_service import (
    DuplicateUserGroupError,
    UserGroupNotFoundError,
    UserGroupService,
)
from application.services.user_service import (
    UserNotFoundError,
    UserService,
)
from application.services.order_service import OrderService
from application.services.product_report_service import ProductReportService
from application.services.product_service import ProductService
from domain.aggregates.order.value_objects import UnverifiedAddress
from domain.exceptions import (
    AddressVerificationError,
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
from domain.user_context import Role, UserContext
from domain.user_info import UserInfo
from infrastructure.django_app.address_verification import get_address_verification_adapter
from infrastructure.django_app.auth_decorators import require_auth
from infrastructure.django_app.metrics import get_metrics_adapter
from domain.user_groups import UserGroup
from infrastructure.django_app.feature_flags import get_feature_flag_repository
from infrastructure.django_app.repositories.user_group_repository import (
    get_user_group_repository,
)
from infrastructure.django_app.repositories.user_repository import (
    get_user_repository,
)
from infrastructure.django_app.readers.product_report_reader import get_product_report_reader
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
    if isinstance(error, AddressVerificationError):
        return Response(
            {"error": str(error), "field": error.field},
            status=status.HTTP_400_BAD_REQUEST,
        )
    # Generic domain error
    return Response(
        {"error": str(error)},
        status=status.HTTP_400_BAD_REQUEST,
    )


# --- Product Endpoints ---


def _get_optional_user_context(request: Request) -> Optional[UserContext]:
    """Get user context if authenticated, None otherwise."""
    if hasattr(request, "user") and request.user.is_authenticated:
        try:
            return build_user_context(request.user)
        except Exception:
            return None
    return None


def _parse_int(value: Optional[str], default: int) -> int:
    """Safely parse an integer from a query parameter."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _parse_decimal(value: Optional[str]) -> Optional[Decimal]:
    """Safely parse a decimal from a query parameter."""
    if value is None:
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _parse_bool(value: Optional[str]) -> Optional[bool]:
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


@api_view(["GET"])
@require_auth
def product_report(request: Request, user_context: UserContext) -> Response:
    """
    Get a product report with cross-aggregate data. Admin only.

    This endpoint demonstrates Simple Query Separation - it bypasses the domain
    layer and uses a dedicated reader to efficiently query data from multiple
    aggregates (Product, Cart, Order) in a single database query.

    Query parameters:
        Pagination:
            page: Page number (1-indexed, default 1)
            page_size: Items per page (default 20, max 100)

        Filters:
            include_deleted: If "true", include soft-deleted products (default: false)
            search: Search term for product name (case-insensitive)
            low_stock_threshold: Only products with stock <= this value
            has_sales: If "true", only products with sales; if "false", only products without sales
            has_reservations: If "true", only products in carts; if "false", only products not in carts

    Returns:
        results: List of products with:
            - product_id, name, price, stock_quantity, is_deleted (from Product)
            - total_sold (sum of quantities from all orders)
            - currently_reserved (sum of quantities in all carts)
        page, page_size, total_count, total_pages, has_next, has_previous: Pagination metadata
    """
    # Parse pagination parameters
    page = _parse_int(request.query_params.get("page"), 1)
    page_size = _parse_int(request.query_params.get("page_size"), 20)

    # Parse filter parameters
    include_deleted = _parse_bool(request.query_params.get("include_deleted")) or False
    search = request.query_params.get("search") or None
    low_stock_threshold_str = request.query_params.get("low_stock_threshold")
    try:
        low_stock_threshold = int(low_stock_threshold_str) if low_stock_threshold_str else None
    except (ValueError, TypeError):
        low_stock_threshold = None
    has_sales = _parse_bool(request.query_params.get("has_sales"))
    has_reservations = _parse_bool(request.query_params.get("has_reservations"))

    query = ProductReportQuery(
        page=page,
        page_size=page_size,
        include_deleted=include_deleted,
        search=search,
        low_stock_threshold=low_stock_threshold,
        has_sales=has_sales,
        has_reservations=has_reservations,
    )

    try:
        service = ProductReportService(get_product_report_reader())
        result = service.get_report(query, user_context)
    except PermissionDeniedError as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_403_FORBIDDEN,
        )

    return Response({
        "results": [
            {
                "product_id": str(item.product_id),
                "name": item.name,
                "price": str(item.price),
                "stock_quantity": item.stock_quantity,
                "is_deleted": item.is_deleted,
                "total_sold": item.total_sold,
                "currently_reserved": item.currently_reserved,
            }
            for item in result.items
        ],
        "page": result.page,
        "page_size": result.page_size,
        "total_count": result.total_count,
        "total_pages": result.total_pages,
        "has_next": result.has_next,
        "has_previous": result.has_previous,
    })


# --- Cart Endpoints ---


@api_view(["GET"])
@require_auth
def cart_get(request: Request, user_context: UserContext) -> Response:
    """Get the current user's cart."""
    with unit_of_work(get_event_dispatcher()) as uow:
        service = CartService(uow, metrics=get_metrics_adapter())
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
        service = CartService(uow, metrics=get_metrics_adapter())
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
        service = CartService(uow, metrics=get_metrics_adapter())
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
        service = CartService(uow, metrics=get_metrics_adapter())
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
def cart_verify_address(request: Request, user_context: UserContext) -> Response:
    """
    Verify a shipping address without submitting the cart.

    Request body:
        street_line_1: str (required)
        street_line_2: str (optional)
        city: str (required)
        state: str (required)
        postal_code: str (required)
        country: str (default: "US")

    Returns:
        verified: bool
        status: str ("verified", "corrected", "invalid", "undeliverable")
        standardized_address: dict (if verified/corrected)
        error_message: str (if invalid/undeliverable)
    """
    with unit_of_work(get_event_dispatcher()) as uow:
        service = CartService(
            uow,
            address_verification=get_address_verification_adapter(),
            metrics=get_metrics_adapter(),
        )
        try:
            data = request.data
            address = UnverifiedAddress(
                street_line_1=data.get("street_line_1", ""),
                street_line_2=data.get("street_line_2"),
                city=data.get("city", ""),
                state=data.get("state", ""),
                postal_code=data.get("postal_code", ""),
                country=data.get("country", "US"),
            )

            verified, result = service.verify_address(address)

            return Response({
                "verified": True,
                "status": result.status.value,
                "standardized_address": verified.to_dict(),
            })
        except AddressVerificationError as e:
            return Response({
                "verified": False,
                "status": "invalid",
                "error_message": str(e),
                "field": e.field,
            }, status=status.HTTP_400_BAD_REQUEST)
        except DomainError as e:
            return handle_domain_error(e)


@api_view(["POST"])
@require_auth
def cart_submit(request: Request, user_context: UserContext) -> Response:
    """
    Submit the user's cart as an order.

    Request body:
        shipping_address:
            street_line_1: str (required)
            street_line_2: str (optional)
            city: str (required)
            state: str (required)
            postal_code: str (required)
            country: str (default: "US")
    """
    with unit_of_work(get_event_dispatcher()) as uow:
        service = CartService(
            uow,
            address_verification=get_address_verification_adapter(),
            metrics=get_metrics_adapter(),
        )
        try:
            data = request.data
            address_data = data.get("shipping_address", {})

            if not address_data:
                return Response(
                    {"error": "shipping_address is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            shipping_address = UnverifiedAddress(
                street_line_1=address_data.get("street_line_1", ""),
                street_line_2=address_data.get("street_line_2"),
                city=address_data.get("city", ""),
                state=address_data.get("state", ""),
                postal_code=address_data.get("postal_code", ""),
                country=address_data.get("country", "US"),
            )

            order = service.submit_cart(
                user_context=user_context,
                shipping_address=shipping_address,
            )
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


# --- Feature Flag Admin Endpoints ---


def _feature_flag_to_dict(flag: FeatureFlag) -> Dict[str, Any]:
    """Convert a FeatureFlag to a dictionary."""
    return {
        "name": flag.name,
        "enabled": flag.enabled,
        "description": flag.description,
        "created_at": flag.created_at.isoformat(),
        "updated_at": flag.updated_at.isoformat(),
        "target_group_ids": [str(gid) for gid in flag.target_group_ids],
    }


def _get_feature_flag_service() -> FeatureFlagService:
    """Get the feature flag service with its dependencies."""
    return FeatureFlagService(get_feature_flag_repository())


@api_view(["GET"])
@require_auth
def feature_flags_list(request: Request, user_context: UserContext) -> Response:
    """List all feature flags. Admin only."""
    try:
        service = _get_feature_flag_service()
        flags = service.get_all(user_context)
        return Response({"results": [_feature_flag_to_dict(f) for f in flags]})
    except PermissionDeniedError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)


@api_view(["POST"])
@require_auth
def feature_flag_create(request: Request, user_context: UserContext) -> Response:
    """Create a new feature flag. Admin only."""
    try:
        service = _get_feature_flag_service()
        data = request.data
        flag = service.create(
            name=data.get("name", ""),
            enabled=data.get("enabled", False),
            description=data.get("description", ""),
            user_context=user_context,
        )
        return Response(_feature_flag_to_dict(flag), status=status.HTTP_201_CREATED)
    except PermissionDeniedError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except DuplicateFeatureFlagError as e:
        return Response(
            {"error": f"Flag '{e.flag_name}' already exists"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["GET", "PUT", "DELETE"])
@require_auth
def feature_flag_detail(
    request: Request, flag_name: str, user_context: UserContext
) -> Response:
    """Get, update, or delete a feature flag. Admin only."""
    try:
        service = _get_feature_flag_service()

        if request.method == "GET":
            flag = service.get_by_name(flag_name, user_context)
            return Response(_feature_flag_to_dict(flag))

        if request.method == "PUT":
            data = request.data
            flag = service.update(
                flag_name=flag_name,
                enabled=data.get("enabled"),
                description=data.get("description"),
                user_context=user_context,
            )
            return Response(_feature_flag_to_dict(flag))

        if request.method == "DELETE":
            service.delete(flag_name, user_context)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    except PermissionDeniedError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except FeatureFlagNotFoundError:
        return Response(
            {"error": f"Flag '{flag_name}' not found"},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["PUT"])
@require_auth
def feature_flag_set_targets(
    request: Request, flag_name: str, user_context: UserContext
) -> Response:
    """
    Set the target groups for a feature flag (replaces existing). Admin only.

    Request body:
        group_ids: List[str] - List of group UUIDs to target
    """
    from uuid import UUID

    try:
        service = _get_feature_flag_service()
        data = request.data
        group_ids_raw = data.get("group_ids", [])
        group_ids = [UUID(gid) for gid in group_ids_raw]
        flag = service.set_target_groups(flag_name, group_ids, user_context)
        return Response(_feature_flag_to_dict(flag))
    except PermissionDeniedError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except FeatureFlagNotFoundError:
        return Response(
            {"error": f"Flag '{flag_name}' not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        return Response({"error": f"Invalid UUID: {e}"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@require_auth
def feature_flag_add_target(
    request: Request, flag_name: str, user_context: UserContext
) -> Response:
    """
    Add a target group to a feature flag. Admin only.

    Request body:
        group_id: str - Group UUID to add as target
    """
    from uuid import UUID

    try:
        service = _get_feature_flag_service()
        data = request.data
        group_id = UUID(data.get("group_id", ""))
        flag = service.add_target_group(flag_name, group_id, user_context)
        return Response(_feature_flag_to_dict(flag))
    except PermissionDeniedError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except FeatureFlagNotFoundError:
        return Response(
            {"error": f"Flag '{flag_name}' not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        return Response({"error": f"Invalid UUID: {e}"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@require_auth
def feature_flag_remove_target(
    request: Request, flag_name: str, group_id: str, user_context: UserContext
) -> Response:
    """Remove a target group from a feature flag. Admin only."""
    from uuid import UUID

    try:
        service = _get_feature_flag_service()
        gid = UUID(group_id)
        flag = service.remove_target_group(flag_name, gid, user_context)
        return Response(_feature_flag_to_dict(flag))
    except PermissionDeniedError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except FeatureFlagNotFoundError:
        return Response(
            {"error": f"Flag '{flag_name}' not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        return Response({"error": f"Invalid UUID: {e}"}, status=status.HTTP_400_BAD_REQUEST)


# --- User Group Admin Endpoints ---


def _user_group_to_dict(group: UserGroup) -> Dict[str, Any]:
    """Convert a UserGroup to a dictionary."""
    return {
        "id": str(group.id),
        "name": group.name,
        "description": group.description,
    }


def _get_user_group_service() -> UserGroupService:
    """Get the user group service with its dependencies."""
    return UserGroupService(get_user_group_repository())


@api_view(["GET"])
@require_auth
def user_groups_list(request: Request, user_context: UserContext) -> Response:
    """List all user groups. Admin only."""
    try:
        service = _get_user_group_service()
        groups = service.get_all(user_context)
        return Response({"results": [_user_group_to_dict(g) for g in groups]})
    except PermissionDeniedError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)


@api_view(["POST"])
@require_auth
def user_group_create(request: Request, user_context: UserContext) -> Response:
    """Create a new user group. Admin only."""
    try:
        service = _get_user_group_service()
        data = request.data
        group = service.create(
            name=data.get("name", ""),
            description=data.get("description", ""),
            user_context=user_context,
        )
        return Response(_user_group_to_dict(group), status=status.HTTP_201_CREATED)
    except PermissionDeniedError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except DuplicateUserGroupError as e:
        return Response(
            {"error": f"Group '{e.name}' already exists"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["GET", "DELETE"])
@require_auth
def user_group_detail(
    request: Request, group_id: str, user_context: UserContext
) -> Response:
    """Get or delete a user group. Admin only."""
    from uuid import UUID

    try:
        service = _get_user_group_service()
        gid = UUID(group_id)

        if request.method == "GET":
            group = service.get_by_id(gid, user_context)
            return Response(_user_group_to_dict(group))

        if request.method == "DELETE":
            service.delete(gid, user_context)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    except PermissionDeniedError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except UserGroupNotFoundError:
        return Response(
            {"error": f"Group '{group_id}' not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        return Response({"error": f"Invalid UUID: {e}"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "POST"])
@require_auth
def user_group_users(
    request: Request, group_id: str, user_context: UserContext
) -> Response:
    """List users in a group or add a user to a group. Admin only."""
    from uuid import UUID

    try:
        service = _get_user_group_service()
        gid = UUID(group_id)

        if request.method == "GET":
            user_ids = service.get_users_in_group(gid, user_context)
            return Response({"user_ids": [str(uid) for uid in user_ids]})

        if request.method == "POST":
            data = request.data
            target_user_id = UUID(data.get("user_id", ""))
            service.add_user(gid, target_user_id, user_context)
            return Response({"status": "added"}, status=status.HTTP_201_CREATED)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    except PermissionDeniedError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except UserGroupNotFoundError:
        return Response(
            {"error": f"Group '{group_id}' not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        return Response({"error": f"Invalid UUID: {e}"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@require_auth
def user_group_remove_user(
    request: Request, group_id: str, target_user_id: str, user_context: UserContext
) -> Response:
    """Remove a user from a group. Admin only."""
    from uuid import UUID

    try:
        service = _get_user_group_service()
        gid = UUID(group_id)
        uid = UUID(target_user_id)
        service.remove_user(gid, uid, user_context)
        return Response(status=status.HTTP_204_NO_CONTENT)
    except PermissionDeniedError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except UserGroupNotFoundError:
        return Response(
            {"error": f"Group '{group_id}' not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        return Response({"error": f"Invalid UUID: {e}"}, status=status.HTTP_400_BAD_REQUEST)


# --- User Management Admin Endpoints ---


def _user_info_to_dict(user: UserInfo) -> Dict[str, Any]:
    """Convert a UserInfo to a dictionary."""
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "group_ids": [str(gid) for gid in user.group_ids],
    }


def _get_user_service() -> UserService:
    """Get the user service with its dependencies."""
    return UserService(get_user_repository(), get_user_group_repository())


@api_view(["GET"])
@require_auth
def users_list(request: Request, user_context: UserContext) -> Response:
    """List all users with their roles and groups. Admin only."""
    try:
        service = _get_user_service()
        users = service.get_all(user_context)
        return Response({"results": [_user_info_to_dict(u) for u in users]})
    except PermissionDeniedError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)


@api_view(["GET", "PUT"])
@require_auth
def user_detail(
    request: Request, user_id: str, user_context: UserContext
) -> Response:
    """Get or update a user's details. Admin only."""
    from uuid import UUID

    try:
        service = _get_user_service()
        uid = UUID(user_id)

        if request.method == "GET":
            user = service.get_by_id(uid, user_context)
            return Response(_user_info_to_dict(user))

        if request.method == "PUT":
            data = request.data
            role_str = data.get("role")
            if role_str:
                try:
                    role = Role(role_str)
                except ValueError:
                    return Response(
                        {"error": f"Invalid role: {role_str}. Must be 'admin' or 'customer'"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                user = service.update_role(uid, role, user_context)
                return Response(_user_info_to_dict(user))
            return Response(
                {"error": "No updates provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    except PermissionDeniedError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except UserNotFoundError:
        return Response(
            {"error": f"User '{user_id}' not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        return Response({"error": f"Invalid UUID: {e}"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@require_auth
def user_add_to_group(
    request: Request, user_id: str, user_context: UserContext
) -> Response:
    """Add a user to a group. Admin only."""
    from uuid import UUID

    try:
        service = _get_user_service()
        uid = UUID(user_id)
        data = request.data
        group_id = UUID(data.get("group_id", ""))
        user = service.add_to_group(uid, group_id, user_context)
        return Response(_user_info_to_dict(user))
    except PermissionDeniedError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except UserNotFoundError:
        return Response(
            {"error": f"User '{user_id}' not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        return Response({"error": f"Invalid UUID: {e}"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@require_auth
def user_remove_from_group(
    request: Request, user_id: str, group_id: str, user_context: UserContext
) -> Response:
    """Remove a user from a group. Admin only."""
    from uuid import UUID

    try:
        service = _get_user_service()
        uid = UUID(user_id)
        gid = UUID(group_id)
        user = service.remove_from_group(uid, gid, user_context)
        return Response(_user_info_to_dict(user))
    except PermissionDeniedError as e:
        return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
    except UserNotFoundError:
        return Response(
            {"error": f"User '{user_id}' not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        return Response({"error": f"Invalid UUID: {e}"}, status=status.HTTP_400_BAD_REQUEST)


# --- Health Check and Metrics ---


@api_view(["GET"])
def health_check(request: Request) -> Response:
    """
    Health check endpoint for load balancers and orchestration systems.

    Checks database connectivity and returns status.
    """
    from datetime import datetime, timezone
    from typing import Any, Dict, List, Optional, Dict

    from django.db import connection

    health_status: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {},
    }

    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)}"

    http_status = status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(health_status, status=http_status)


@api_view(["GET"])
def metrics(request: Request) -> Response:
    """
    Metrics endpoint exposing application metrics in Prometheus format.

    Returns counters for HTTP requests, errors, and domain events.
    """
    from infrastructure.django_app.metrics import get_metrics

    metrics_output = get_metrics().to_prometheus()
    return Response(metrics_output, content_type="text/plain; charset=utf-8")


# --- Debug/Test Endpoints ---


@api_view(["POST"])
@require_auth
def trigger_test_error(request: Request, user_context: UserContext) -> Response:
    """
    Test endpoint to trigger a 500 error for testing incident notifications.

    Admin only. Raises an exception to test the incident notification middleware.

    Note: Authorization is intentionally in the view (not application service) because
    this is a test utility endpoint with no business logic - it only exists to trigger
    an error for testing the incident notification middleware.
    """
    if not user_context.is_admin():
        return Response(
            {"error": "Only admins can trigger test errors"},
            status=status.HTTP_403_FORBIDDEN,
        )
    raise Exception("Test error triggered for incident notification testing")
