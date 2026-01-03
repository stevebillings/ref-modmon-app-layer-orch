# Authentication and Authorization

This document describes the authentication and authorization implementation for the reference web application.

## Overview

The application uses Django session-based authentication with role-based access control (RBAC). The design keeps auth concerns out of domain logic by introducing a `UserContext` abstraction in the domain layer.

## Key Design Decisions

### 1. Django Sessions (not JWT)

We chose Django's built-in session authentication for simplicity:
- Server-side session storage
- Automatic CSRF protection
- Works well with the existing Django infrastructure

### 2. UserContext Pattern

The `UserContext` dataclass in the domain layer provides a framework-agnostic representation of the authenticated user:

```python
@dataclass(frozen=True)
class UserContext:
    user_id: UUID
    username: str
    role: Role  # Enum: ADMIN, CUSTOMER

    def is_admin(self) -> bool
    def is_customer(self) -> bool

    @property
    def actor_id(self) -> str  # For domain event audit logging
```

This keeps the domain layer free of Django dependencies while allowing authorization decisions in the application layer.

### 3. Authorization in Application Layer

Permission checks happen in application services, not in the domain layer or views:

```python
class ProductService:
    def create_product(self, ..., user_context: UserContext) -> Product:
        if not user_context.is_admin():
            raise PermissionDeniedError("create_product", "Only administrators can create products")
        # ... proceed with creation
```

### 4. Roles

Two roles are defined:
- **Admin**: Can create/delete products, view all orders
- **Customer**: Can manage their own cart, view their own orders

## Architecture

### Layer Responsibilities

| Layer | Auth Concern | Django Dependency |
|-------|-------------|-------------------|
| Domain | None | None |
| Application | UserContext (authorization checks) | None |
| Infrastructure | Session handling, UserContext conversion | Yes |

### Data Flow

```
HTTP Request with Session Cookie
    │
    ▼
Django SessionMiddleware (extracts user)
    │
    ▼
@require_auth decorator
    │ Converts Django User → UserContext
    ▼
View Function
    │ Passes UserContext to application service
    ▼
Application Service
    │ Checks permissions using UserContext
    │ Uses user_context.actor_id for domain events
    ▼
Domain Aggregates (auth-unaware)
```

## API Endpoints

### Auth Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login/` | POST | Login with username/password |
| `/api/auth/logout/` | POST | End session |
| `/api/auth/session/` | GET | Get current session status and CSRF token |

### Authorization Matrix

| Endpoint | Anonymous | Customer | Admin |
|----------|-----------|----------|-------|
| GET /products/ | Yes | Yes | Yes |
| POST /products/create/ | No | No | Yes |
| DELETE /products/{id}/ | No | No | Yes |
| GET /cart/ | No | Own | Own |
| POST /cart/items/ | No | Own | Own |
| PATCH /cart/items/{id}/ | No | Own | Own |
| DELETE /cart/items/{id}/remove/ | No | Own | Own |
| POST /cart/submit/ | No | Own | Own |
| GET /orders/ | No | Own only | All |

## Implementation Files

### Domain Layer
- `domain/user_context.py` - UserContext and Role
- `domain/exceptions.py` - PermissionDeniedError

### Infrastructure Layer
- `infrastructure/django_app/models.py` - UserProfile model
- `infrastructure/django_app/auth_views.py` - Login/logout/session endpoints
- `infrastructure/django_app/user_context_adapter.py` - Django User → UserContext conversion
- `infrastructure/django_app/auth_decorators.py` - @require_auth decorator

### Frontend
- `contexts/AuthContext.tsx` - React auth context and useAuth hook
- `components/ProtectedRoute.tsx` - Route protection component
- `pages/LoginPage.tsx` - Login form

## Multi-User Support

The application now supports multiple users:
- Each user has their own cart
- Orders are associated with the user who placed them
- Cart and Order models include a `user_id` field

## Default Users

A default admin user is created during migration:
- Username: `admin`
- Password: `admin`
- Role: Admin

Additional users can be created via Django admin or management commands.
