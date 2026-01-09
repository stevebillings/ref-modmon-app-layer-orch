# Reference Web Application

A reference e-commerce web application demonstrating architectural patterns for medium-complexity applications developed by small teams. This project serves as a practical example of how to structure a **Domain-Driven Design (DDD) Modular Monolith** with **Hexagonal Architecture** and **Application Layer Orchestration**.

## Purpose

This application is intentionally kept simple enough to understand while demonstrating solutions to common web application problems. Use it as a reference when building real applications that need clean architecture, maintainability, and testability.

For detailed architecture documentation, see [specs/ARCHITECTURE.md](specs/ARCHITECTURE.md).

## Technology Stack

- **Backend**: Python 3.12+ / Django 6.0 / Django REST Framework
- **Frontend**: TypeScript / React 19 / Chakra UI
- **Database**: SQLite (development)

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Email Configuration (Optional)

To enable real email sending (e.g., for incident notifications), configure Gmail SMTP:

1. Copy the example environment file:
   ```bash
   cp backend/.env.example backend/.env
   ```

2. Edit `backend/.env` with your Gmail credentials:
   ```
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```

3. **Important**: You need a Gmail App Password, not your regular password:
   - Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
   - Generate an app password for "Mail"
   - Use that 16-character password in `EMAIL_HOST_PASSWORD`

Without these settings, emails are printed to the console (development mode).

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Default Login

- **Username**: `admin`
- **Password**: `admin`

## Problems and Solutions Demonstrated

This reference application demonstrates solutions to common architectural challenges in web applications:

### 1. Separation of Concerns

**Problem**: Business logic gets tangled with framework code, database access, and HTTP handling, making the codebase hard to test and maintain.

**Solution**: **Layered Architecture** with clear boundaries:

| Layer | Responsibility | Dependencies |
|-------|---------------|--------------|
| Domain | Business logic, entities, validation | None (pure Python) |
| Application | Use case orchestration, authorization | Domain only |
| Infrastructure | Framework integration, persistence, APIs | All layers |

The `domain/` directory contains zero Django imports. Business rules can be tested without spinning up a web server or database.

### 2. Framework Independence

**Problem**: Over-reliance on framework features creates vendor lock-in and makes the codebase harder to port or test.

**Solution**: **Hexagonal Architecture (Ports & Adapters)**

- **Ports**: Abstract interfaces defined in domain/application layers (e.g., `RepositoryInterface`, `FeatureFlagPort`, `EmailPort`)
- **Adapters**: Framework-specific implementations in infrastructure (e.g., `DjangoProductRepository`, `DjangoFeatureFlagAdapter`)

The application layer depends only on interfaces. Swap Django for Flask by writing new adapters—the domain and application layers remain unchanged.

### 3. Cross-Aggregate Coordination

**Problem**: Operations spanning multiple aggregates (e.g., "add item to cart" affects both Cart and Product) need coordination while maintaining consistency.

**Solution**: **Application Layer Orchestration** with **Unit of Work**

```python
def add_item(self, product_id: str, quantity: int, user_context: UserContext) -> Cart:
    # Lock product to prevent concurrent stock changes
    product = self.uow.get_product_repository().get_by_id_for_update(product_id)

    # Coordinate both aggregates
    cart.add_item(product_id, product.name, product.price, quantity)
    product.reserve_stock(quantity)

    # Single transaction commits both changes
    self.uow.get_cart_repository().save(cart)
    self.uow.get_product_repository().save(product)
```

All changes within a request happen in a single database transaction, ensuring strong consistency.

### 4. Aggregate Isolation

**Problem**: Aggregates that directly reference each other become tightly coupled and hard to evolve independently.

**Solution**: **Reference by ID + Snapshot Pattern**

Aggregates never embed or import other aggregates. They reference other aggregates by ID only:

```python
@dataclass(frozen=True)
class CartItem:
    product_id: UUID      # Reference by ID, not embedded Product
    product_name: str     # Snapshot: copied when item added
    unit_price: Decimal   # Snapshot: price at time of addition
```

If a product's price changes later, cart items retain the original price. If a product is deleted, order history remains intact.

### 5. Domain Events and Audit Logging

**Problem**: Cross-cutting concerns like audit logging pollute domain logic. Tightly coupled event handling creates fragile systems.

**Solution**: **Domain Events with Post-Commit Dispatch**

Aggregates raise events internally:
```python
def reserve_stock(self, quantity: int, actor_id: str) -> None:
    self.stock_quantity -= quantity
    self._raise_event(StockReserved(product_id=self.id, quantity=quantity, actor_id=actor_id))
```

Events are dispatched after the transaction commits. Handlers (sync or async) process them independently:
- **Sync handlers**: Audit logging (fast, critical)
- **Async handlers**: Email notifications (slow, non-blocking)

Handler failures are logged but don't break the business operation.

### 6. Cross-Aggregate Queries (Simple Query Separation)

**Problem**: Reporting and dashboard queries need to aggregate data from multiple aggregates. Forcing these through the domain layer is awkward and inefficient - aggregates are designed for write consistency, not read optimization.

**Solution**: **Simple Query Separation** - treat reads and writes differently

Commands (writes) go through the domain:
```
API → Application Service → Aggregates → Repository → DB
```

Cross-aggregate queries bypass the domain:
```
API → Reader → DB (direct joins/aggregations)
```

Example: Product report combining data from Product, Cart, and Order aggregates:
```python
class DjangoProductReportReader(ProductReportReader):
    def get_report(self, query: ProductReportQuery) -> list[ProductReportItem]:
        # Single query with subqueries aggregating from related tables
        queryset = ProductModel.objects.annotate(
            total_sold=Coalesce(Subquery(order_items_sum), 0),
            currently_reserved=Coalesce(Subquery(cart_items_sum), 0),
        )
        return [self._to_report_item(p) for p in queryset]
```

Benefits:
- **Queries don't need aggregates** - no invariants to enforce for reads
- **Efficient** - single optimized database query with joins
- **Simpler than full CQRS** - no separate read database or event projections
- **Clean separation** - domain stays focused on business rules

### 7. Authentication Without Domain Pollution

**Problem**: Authentication concerns (sessions, tokens, user objects) leak into domain logic, coupling it to the web framework.

**Solution**: **UserContext Pattern**

The domain layer defines a framework-agnostic `UserContext`:
```python
@dataclass(frozen=True)
class UserContext:
    user_id: UUID
    username: str
    role: Role  # ADMIN or CUSTOMER
    group_ids: frozenset[UUID]  # For feature flag targeting
```

Infrastructure converts Django's User to UserContext, including group memberships. Application services receive UserContext for authorization decisions and feature flag targeting. The domain layer remains completely auth-unaware.

### 8. Frontend Authorization Without HATEOAS

**Problem**: The frontend needs to know what actions the current user can perform to show/hide UI elements. Full HATEOAS (embedding action links in every response) is complex to implement and often ignored by SPAs anyway.

**Solution**: **Role-Based Capabilities**

The API returns a `capabilities` list with the user object at login:
```json
{
  "user": {
    "id": "...",
    "username": "admin",
    "role": "admin",
    "capabilities": ["products:create", "products:delete", "orders:view_all", ...]
  }
}
```

Capabilities are derived from the user's role in the domain layer:
```python
class Capability(Enum):
    PRODUCTS_CREATE = "products:create"
    PRODUCTS_DELETE = "products:delete"
    # ...

ROLE_CAPABILITIES = {
    Role.ADMIN: frozenset({Capability.PRODUCTS_CREATE, Capability.PRODUCTS_DELETE, ...}),
    Role.CUSTOMER: frozenset({Capability.PRODUCTS_VIEW, Capability.CART_MODIFY, ...}),
}
```

The frontend uses a `RequireCapability` component for clean conditional rendering:
```tsx
<RequireCapability capability={Capabilities.PRODUCTS_CREATE}>
  <CreateProductButton />
</RequireCapability>
```

Benefits:
- **Simple**: Single request gets all permissions upfront
- **Type-safe**: Frontend uses constants, not string literals
- **Cacheable**: Frontend can cache capabilities for the session
- **Pragmatic**: Avoids HATEOAS complexity while solving the same problem

### 9. Concurrency Control

**Problem**: Concurrent requests can corrupt data (overselling stock, duplicate records, lost updates).

**Solution**: **Multiple Patterns Based on Scenario**

| Scenario | Pattern | Implementation |
|----------|---------|----------------|
| Read-then-modify | Row-level locking | `select_for_update()` |
| Singleton creation | Atomic get-or-create | `get_or_create()` |
| Uniqueness validation | DB constraint + fallback | Unique constraint + catch `IntegrityError` |

### 10. Feature Flags with User Group Targeting

**Problem**: Deploying new features requires code changes. Rolling back problematic features means redeploying. Rolling out features gradually to specific users is difficult without complex deployment strategies.

**Solution**: **Feature Flag System with User Group Targeting**

- Port interface: `FeatureFlagPort.is_enabled(flag_name, user_context)`
- Database adapter: Stores flags with optional target groups
- Admin API: CRUD operations for flags, groups, and targeting
- Fail-safe defaults: Unknown flags return `false`

**Targeting Logic**:
```python
def is_enabled(flag_name, user_context):
    # Master kill switch - if disabled, always False
    if not flag.enabled:
        return False
    # No target groups - enabled for everyone
    if not flag.target_groups:
        return True
    # With target groups - check user membership
    return user_context and user_in_any_target_group(user_context, flag.target_groups)
```

**User Groups vs Roles**:
- **Roles** are for authorization (what you CAN do): Admin, Customer
- **Groups** are for targeting (what you SEE): beta_testers, internal_users, power_users

A customer can be in the "beta_testers" group without gaining admin privileges. This enables gradual rollouts, A/B testing, and feature gating without coupling to the authorization model.

### 11. Soft Delete with History Preservation

**Problem**: Hard deletes lose data permanently. Deleting products breaks order history.

**Solution**: **Soft Delete + Snapshot Pattern**

- Products have `deleted_at` timestamp (null = active)
- Soft-deleted products hidden from catalog but remain in database
- Order items store product name and price as snapshots
- Admins can view and restore soft-deleted products

### 12. Use Case Documentation and Testing

**Problem**: Use cases live in developers' heads or scattered documentation. No single source of truth connects requirements, tests, and domain language. New team members struggle to understand what the system does.

**Solution**: **Behavior Driven Development (BDD) with pytest-bdd**

Feature files document use cases in Gherkin syntax using the project's ubiquitous language:
```gherkin
Feature: Add Item to Cart
  As a Customer
  I want to add products to my cart
  So that I can purchase them later

  Scenario: Successfully add item to cart
    Given I am logged in as a Customer
    And a product "Laptop" exists with price "$999.99" and stock quantity 10
    When I add 2 "Laptop" to my cart
    Then my cart should contain 2 "Laptop" at "$999.99" each
    And the product "Laptop" should have stock quantity 8
```

Benefits:
- **Living documentation** - Feature files are both requirements and executable tests
- **Ubiquitous language** - Scenarios use domain terms from [GLOSSARY.md](specs/GLOSSARY.md)
- **Use case traceability** - Each scenario maps to a specific user action
- **Onboarding aid** - New developers understand behavior by reading features

See [BDD-APPROACH.md](specs/BDD-APPROACH.md) for full details.

### 13. Third-Party API Integration

**Problem**: External service integrations (payment processors, address verification, shipping APIs) tightly couple infrastructure code to business logic, making testing difficult and creating vendor lock-in.

**Solution**: **Port/Adapter Pattern for External Services**

Define a port interface in the application layer:
```python
class AddressVerificationPort(ABC):
    @abstractmethod
    def verify(self, street, city, state, postal_code, country) -> AddressVerificationResult:
        pass
```

Implement adapters in infrastructure:
```python
class StubAddressVerificationAdapter(AddressVerificationPort):
    """Stub for development/testing."""
    def verify(self, ...) -> AddressVerificationResult:
        # Returns standardized address or validation errors

class USPSAddressVerificationAdapter(AddressVerificationPort):
    """Real adapter using USPS API."""
    def verify(self, ...) -> AddressVerificationResult:
        # HTTP client calls to USPS service
```

Benefits:
- **Testability**: Use stub adapter in tests without network calls
- **Flexibility**: Swap providers (USPS → SmartyStreets) by changing adapter
- **Fail-closed**: Reject operations if external service unavailable
- **Separation**: Business logic doesn't know about HTTP, retries, or API keys

### 14. Monitoring and Observability

**Problem**: Production applications need visibility into health, performance, and behavior. Without structured logging, request correlation, and metrics, debugging issues across distributed operations becomes extremely difficult.

**Solution**: **Layered Observability with Request Correlation**

| Component | Purpose | Endpoint/Location |
|-----------|---------|-------------------|
| Health Check | Liveness/readiness probes | `GET /api/health/` |
| Metrics | Prometheus-format counters, gauges, histograms | `GET /api/metrics/` |
| Structured Logging | JSON logs with consistent fields | `JSONFormatter` |
| Request Correlation | Track requests across all operations | `X-Request-ID` header |

**Request ID Correlation**: Every request gets a unique ID (from `X-Request-ID` header or auto-generated). This ID flows through:
- All log entries via `request_id` field
- Domain event dispatch and audit logs
- Response header for client-side correlation

```python
# Request context using Python's contextvars (thread-safe)
_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

# Middleware sets it at request start
request_id = request.META.get("HTTP_X_REQUEST_ID") or generate_request_id()
set_request_id(request_id)

# Available anywhere in the request lifecycle
logger.info("Processing order", extra={"request_id": get_request_id()})
```

**Cross-Aggregate Operation Timing**: Application services instrument multi-aggregate operations:
```python
def add_item(self, product_id: str, quantity: int, user_context: UserContext) -> Cart:
    with time_operation("cart_add_item"):
        # Coordinates Cart and Product aggregates
        # Duration recorded to metrics as histogram
```

Benefits:
- **Debuggability**: Trace any request through logs, events, and metrics
- **Production-ready**: Health checks for container orchestration
- **Standards-based**: Prometheus metrics format for monitoring tools
- **DDD-aware**: Timing specifically targets cross-aggregate operations

### 15. Architecture Enforcement

**Problem**: Software architectures erode over time. Developers (or AI assistants) inadvertently add imports that violate layer boundaries—domain importing from infrastructure, aggregates importing from each other—creating tight coupling that undermines the architecture's benefits.

**Solution**: **Automated Import Linting with import-linter**

Define architectural contracts in `.importlinter`:
```ini
[importlinter:contract:domain-layer-independence]
name = Domain layer must not import from application or infrastructure
type = forbidden
source_modules = domain
forbidden_modules = application, infrastructure, django

[importlinter:contract:cart-aggregate-isolation]
name = Cart aggregate must not import from other aggregates
type = forbidden
source_modules = domain.aggregates.cart
forbidden_modules = domain.aggregates.product, domain.aggregates.order
```

Run `lint-imports` to verify:
```
Contracts: 5 kept, 0 broken.
```

Benefits:
- **Automated enforcement**: Violations caught immediately, not in code review
- **Self-documenting**: Contracts serve as architecture documentation
- **CI-ready**: Add to build pipeline to block violating PRs
- **Granular control**: Enforce both layer boundaries and aggregate isolation

## Project Structure

```
project-root/
├── backend/
│   ├── domain/                 # Pure business logic (NO Django)
│   │   ├── aggregates/         # Product, Cart, Order
│   │   ├── events.py           # Base DomainEvent class
│   │   └── user_context.py     # Auth abstraction
│   ├── application/            # Use case orchestration
│   │   ├── ports/              # Interface definitions
│   │   └── services/           # Application services
│   └── infrastructure/         # Framework-dependent code
│       ├── events/             # Event dispatcher
│       └── django_app/         # Django implementation
├── frontend/
│   └── src/
│       ├── components/         # Reusable UI components
│       ├── constants/          # Shared constants (e.g., capabilities)
│       ├── contexts/           # React contexts (e.g., AuthContext)
│       ├── pages/              # Page components
│       ├── services/           # API client
│       └── types/              # TypeScript types
└── specs/                      # Architecture documentation
```

## Running Tests

### Backend
```bash
cd backend
python -m pytest
```

### Frontend
```bash
cd frontend
npm test
```

## Documentation

- [Architecture](specs/ARCHITECTURE.md) - Detailed architectural patterns
- [Design](specs/DESIGN.md) - API design and data entities
- [Requirements](specs/REQUIREMENTS.md) - Functional requirements
- [Glossary](specs/GLOSSARY.md) - Ubiquitous language and domain terms
- [BDD Approach](specs/BDD-APPROACH.md) - Behavior Driven Development testing
- [Domain Events](specs/features/DOMAIN-EVENTS-AND-AUDIT-LOGGING.md) - Event system implementation
- [Authentication](specs/features/AUTHENTICATION-AND-AUTHORIZATION.md) - Auth implementation
- [Feature Flags](specs/features/FEATURE-FLAGS-AND-INCIDENT-NOTIFICATION.md) - Feature flag system
- [Soft Delete](specs/features/SOFT-DELETE.md) - Soft delete implementation
- [Address Verification](specs/features/ADDRESS-VERIFICATION.md) - Third-party API integration pattern

## Future Considerations

The following are intentionally deferred to keep the implementation simple:

- **Value Objects**: Wrapping primitives (Money, Quantity) for type safety
- **API Specification**: OpenAPI/Swagger for contract-first development
- **Dependency Injection Framework**: Currently using manual DI
- **One Django App Per Aggregate**: Currently using single app for simplicity

See [ARCHITECTURE.md](specs/ARCHITECTURE.md#future-considerations) for trade-off analysis.
