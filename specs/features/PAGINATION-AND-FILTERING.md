# Pagination and Filtering Implementation

## Overview

This document describes the implementation of pagination and filtering for the product catalog. This is a common requirement in web applications that touches all layers (API, Application, Domain, Infrastructure) while maintaining clean architecture principles.

## Architecture

### Request Flow

```
API Request with Query Parameters
    ↓
View parses parameters (page, page_size, search, etc.)
    ↓
ProductService.get_products_paginated()
    ↓
ProductRepository.find_paginated() with ProductFilter
    ↓
Django ORM builds and executes query
    ↓
PaginatedResult returned with items and metadata
    ↓
JSON response with results and pagination info
```

### Key Design Decisions

1. **Domain Types**: `ProductFilter` and `PaginatedResult` are defined in the domain layer as they represent domain concepts (search criteria, page of results), not infrastructure concerns.

2. **Generic PaginatedResult**: Uses Python generics (`PaginatedResult[T]`) so it can be reused for any paginated aggregate query.

3. **Repository Method**: The repository interface defines `find_paginated()` to keep pagination logic in the data access layer where it belongs.

4. **Service Layer Validation**: The service enforces limits (max page_size=100) and normalizes inputs (page minimum=1).

5. **Public Endpoint**: Product listing remains a public endpoint (no authentication required) as the catalog is publicly browsable.

## Domain Layer

### Filter Criteria

Location: `backend/domain/pagination.py`

```python
@dataclass(frozen=True)
class ProductFilter:
    search: str | None = None       # Case-insensitive name search
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    in_stock: bool | None = None    # Only products with stock > 0
```

The filter is immutable (frozen dataclass) and all fields are optional. Unset fields mean no filtering on that dimension.

### Paginated Result

Location: `backend/domain/pagination.py`

```python
@dataclass(frozen=True)
class PaginatedResult(Generic[T]):
    items: list[T]
    total_count: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int: ...
    @property
    def has_next(self) -> bool: ...
    @property
    def has_previous(self) -> bool: ...
```

The result includes both the items and metadata needed for pagination controls.

## Repository Interface

Location: `backend/domain/aggregates/product/repository.py`

```python
@abstractmethod
def find_paginated(
    self,
    page: int = 1,
    page_size: int = 20,
    filter: ProductFilter | None = None,
) -> PaginatedResult[Product]:
    """Find products with pagination and optional filtering."""
    pass
```

The repository interface remains framework-agnostic. Implementations (Django, etc.) handle the specifics.

## Infrastructure Layer

### Django Repository Implementation

Location: `backend/infrastructure/django_app/repositories/product_repository.py`

The implementation:
1. Builds a Django QuerySet from the model
2. Applies filters using Django's ORM (icontains, gte, lte, etc.)
3. Counts total matching records
4. Slices for the current page
5. Converts models to domain entities

```python
def find_paginated(self, page: int = 1, page_size: int = 20,
                   filter: ProductFilter | None = None) -> PaginatedResult[Product]:
    queryset = ProductModel.objects.all()
    if filter:
        queryset = self._apply_filter(queryset, filter)
    total_count = queryset.count()
    offset = (page - 1) * page_size
    models = list(queryset[offset : offset + page_size])
    return PaginatedResult(
        items=[self._to_domain(m) for m in models],
        total_count=total_count,
        page=page,
        page_size=page_size,
    )
```

## Application Layer

### Service Method

Location: `backend/application/services/product_service.py`

```python
def get_products_paginated(
    self,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    in_stock: bool | None = None,
) -> PaginatedResult[Product]:
```

The service:
- Accepts individual filter parameters (cleaner API than passing a filter object)
- Enforces limits (page >= 1, page_size between 1 and 100)
- Constructs the filter object only if any criteria are provided
- Delegates to repository

## API Layer

### View with Query Parameters

Location: `backend/infrastructure/django_app/views.py`

The view parses query parameters safely:

```python
@api_view(["GET"])
def products_list(request: Request) -> Response:
    page = _parse_int(request.query_params.get("page"), 1)
    page_size = _parse_int(request.query_params.get("page_size"), 20)
    search = request.query_params.get("search") or None
    min_price = _parse_decimal(request.query_params.get("min_price"))
    max_price = _parse_decimal(request.query_params.get("max_price"))
    in_stock = _parse_bool(request.query_params.get("in_stock"))

    result = service.get_products_paginated(...)

    return Response({
        "results": [...],
        "page": result.page,
        "page_size": result.page_size,
        "total_count": result.total_count,
        "total_pages": result.total_pages,
        "has_next": result.has_next,
        "has_previous": result.has_previous,
    })
```

### Response Format

```json
{
  "results": [
    {"id": "...", "name": "Product A", "price": "19.99", "stock_quantity": 50},
    ...
  ],
  "page": 1,
  "page_size": 20,
  "total_count": 100,
  "total_pages": 5,
  "has_next": true,
  "has_previous": false
}
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number (1-indexed) |
| page_size | int | 20 | Items per page (max 100) |
| search | string | - | Case-insensitive name search |
| min_price | decimal | - | Minimum price filter |
| max_price | decimal | - | Maximum price filter |
| in_stock | bool | - | If true, only items with stock > 0 |

### Example Requests

```bash
# Basic pagination
GET /api/products/?page=2&page_size=10

# Search with filter
GET /api/products/?search=laptop&min_price=500&max_price=1500

# In-stock items only
GET /api/products/?in_stock=true

# Combined
GET /api/products/?search=widget&min_price=20&in_stock=true&page_size=5
```

## Testing Strategy

1. **Unit Tests**: PaginatedResult properties (total_pages, has_next, etc.)
2. **API Tests**: Full flow through all layers with various filter combinations
3. **Test Data**: Use `python manage.py seed_products --count 100` to generate test data

### Test Coverage

- `test_pagination_defaults`: Verifies default values
- `test_pagination_custom_page_size`: Custom page sizes
- `test_pagination_second_page`: Navigation between pages
- `test_pagination_last_page`: Partial pages
- `test_filter_by_search`: Name search
- `test_filter_by_min_price`: Minimum price filter
- `test_filter_by_max_price`: Maximum price filter
- `test_filter_by_price_range`: Combined price range
- `test_filter_in_stock`: Stock availability filter
- `test_combined_filters_and_pagination`: All features together

## Test Data Seeding

A Django management command generates test products:

```bash
# Default: 50 products
python manage.py seed_products

# Custom count
python manage.py seed_products --count 100

# Clear existing and reseed
python manage.py seed_products --clear --count 50
```

Location: `backend/infrastructure/django_app/management/commands/seed_products.py`

## Future Enhancements

1. **Sorting**: Add `sort_by` and `sort_order` parameters
2. **Category Filter**: If categories are added to products
3. **Full-Text Search**: Replace icontains with PostgreSQL full-text search
4. **Cursor Pagination**: For very large datasets or real-time updates
5. **Caching**: Cache common queries for performance
