# Implementation Plan

This document outlines the implementation plan for the e-commerce application.

## Phase 1: Project Setup

1. **Backend project initialization**
   - Create Django project structure with the specified directory layout (domain/, application/, infrastructure/)
   - Configure Django settings for development (SQLite database, CORS for local React dev server)
   - Install dependencies: Django, Django REST Framework, django-cors-headers, pytest, pytest-django

2. **Frontend project initialization**
   - Create React app with TypeScript using Vite
   - Set up directory structure (components/, pages/, services/, types/)
   - Install dependencies: React Router, Chakra UI, Jest + React Testing Library

## Phase 2: Backend Domain Layer (no Django dependencies)

3. **Domain entities**
   - `domain/aggregates/product/entity.py` - Product frozen dataclass
   - `domain/aggregates/cart/entities.py` - Cart and CartItem frozen dataclasses
   - `domain/aggregates/order/entities.py` - Order and OrderItem frozen dataclasses

4. **Repository interfaces**
   - `domain/aggregates/product/repository.py` - Abstract base class defining CRUD operations
   - `domain/aggregates/cart/repository.py` - Abstract base class defining CRUD operations
   - `domain/aggregates/order/repository.py` - Abstract base class defining CRUD operations

5. **Domain validation**
   - Validation logic for each entity (price constraints, quantity limits, etc.)
   - Custom domain exceptions (e.g., `DuplicateProductError`, `InsufficientStockError`, `ValidationError`)

6. **Domain layer tests**
   - pytest tests for entity creation and validation

## Phase 3: Backend Infrastructure Layer

7. **Django ORM models**
   - `infrastructure/django_app/models.py` - Product, Cart, CartItem, Order, OrderItem models
   - Unique constraint on Product name
   - Foreign key relationships and constraints

8. **Repository implementations**
   - `infrastructure/django_app/repositories/product_repository.py` - Django ORM implementation
   - `infrastructure/django_app/repositories/cart_repository.py` - Django ORM implementation
   - `infrastructure/django_app/repositories/order_repository.py` - Django ORM implementation
   - Mapping between ORM models and domain entities

9. **Unit of Work**
   - `infrastructure/django_app/unit_of_work.py` - Transaction management wrapper

10. **Utility functions**
    - `to_dict()` recursive conversion function for serializing domain entities

11. **Infrastructure layer tests**
    - pytest tests for repository implementations (using test database)
    - pytest tests for `to_dict()` conversion

## Phase 4: Backend Application Layer

12. **Application services**
    - `application/services/product_service.py` - Create, list, delete products
    - `application/services/cart_service.py` - Add/remove/update cart items, submit cart (cross-aggregate orchestration)
    - `application/services/order_service.py` - List orders

13. **Application layer tests**
    - pytest tests for application services with mocked repositories
    - Tests for cross-aggregate operations (stock reservation, cart submission)

## Phase 5: Backend API Layer

14. **Django views**
    - `infrastructure/django_app/views.py` - REST endpoints for all API operations
    - Request parsing and response formatting using `to_dict()`

15. **URL routing**
    - Configure URL patterns for all endpoints

16. **Database migrations**
    - Generate and apply initial migrations

17. **API integration tests**
    - pytest tests for all endpoints
    - Tests for validation error responses
    - Tests for cross-aggregate operation side effects (stock changes)

## Phase 6: Frontend Foundation

18. **TypeScript types**
    - `types/` - Product, Cart, CartItem, Order, OrderItem interfaces matching API responses

19. **API service layer**
    - `services/api.ts` - Functions for all API calls

20. **Currency utilities**
    - `services/currencyUtils.ts` - Format prices for display

21. **Frontend utility tests**
    - Jest tests for currency formatting functions

## Phase 7: Frontend Components

22. **Shared components**
    - ConfirmationDialog - Chakra UI Modal wrapper for delete confirmations
    - ErrorAlert - Display API/validation errors

23. **Product components**
    - ProductList - Display list with delete buttons and Add to Cart controls
    - ProductForm - Create form with validation

24. **Cart components**
    - CartView - Display cart items with quantity controls and remove buttons
    - SubmitOrderButton - Submit cart as order

25. **Order components**
    - OrderList - Display order history with details

26. **Component tests**
    - Jest + React Testing Library tests for key component behaviors

## Phase 8: Frontend Pages

27. **Page components**
    - Landing page with navigation and cart item count
    - Product Catalog page (list + create form + add to cart)
    - Cart page (cart view + quantity adjustments + submit)
    - Order History page (order list)

28. **Routing**
    - React Router configuration

29. **Page tests**
    - Jest tests for page rendering and navigation

## Phase 9: Integration & Polish

30. **End-to-end verification**
    - Manual verification of all flows: create/delete products, add/remove/update cart items, submit orders
    - Verify stock reservation and release behavior
    - Verify validation errors display correctly

31. **Empty states and error handling**
    - Implement empty state messages
    - Handle API errors gracefully

---

## Key Dependencies

- Phase 2 (domain) has no dependencies
- Phase 3 (infrastructure) depends on Phase 2
- Phase 4 (application) depends on Phases 2 & 3
- Phase 5 (API) depends on Phase 4
- Phase 6 (frontend types/services) can start after Phase 5 API design is clear
- Phases 7-8 (frontend UI) depend on Phase 6

## Technology Choices

- **Backend**: Python/Django, Django REST Framework, SQLite (dev), pytest
- **Frontend**: TypeScript, React, Vite, Chakra UI, Jest + React Testing Library
- **CSS Framework**: Chakra UI (React component library with built-in styling)
