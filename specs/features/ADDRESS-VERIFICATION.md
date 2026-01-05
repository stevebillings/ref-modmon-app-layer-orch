# Address Verification

This document specifies the address verification integration, demonstrating how to wrap a third-party HTTP API behind a port in a DDD modular monolith.

## Overview

Address verification validates shipping addresses before order submission. This integration demonstrates:

1. **Port/adapter pattern for HTTP APIs** - Clean separation between domain logic and external service
2. **Request/response mapping** - Translating between domain and external API formats
3. **Structured error handling** - Domain-specific exceptions for verification failures
4. **Fail-closed behavior** - Reject orders if verification fails or service unavailable

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│                                                              │
│  ┌──────────────────┐     ┌────────────────────────────┐    │
│  │  CartService     │     │  AddressVerificationPort   │    │
│  │                  │────▶│  (interface)               │    │
│  │  verify_address()│     │                            │    │
│  │  submit_cart()   │     │  verify(street, city, ...) │    │
│  └──────────────────┘     └─────────────┬──────────────┘    │
│                                         │                    │
└─────────────────────────────────────────┼────────────────────┘
                                          │
┌─────────────────────────────────────────┼────────────────────┐
│ Infrastructure Layer                    │                    │
│                                         ▼                    │
│           ┌────────────────────────────────────────┐         │
│           │  StubAddressVerificationAdapter        │         │
│           │                                        │         │
│           │  - Returns VERIFIED for normal addrs   │         │
│           │  - Returns INVALID for test triggers   │         │
│           │  - Returns UNDELIVERABLE for test      │         │
│           │  - Standardizes address format         │         │
│           └────────────────────────────────────────┘         │
│                                                              │
│  (Future: RealAddressVerificationAdapter using HTTP client)  │
└──────────────────────────────────────────────────────────────┘
```

## Domain Layer

### Value Objects

Located at `domain/aggregates/order/value_objects.py`:

```python
@dataclass(frozen=True)
class UnverifiedAddress:
    """Address input from user, not yet verified."""
    street_line_1: str
    street_line_2: str | None
    city: str
    state: str
    postal_code: str
    country: str

@dataclass(frozen=True)
class VerifiedAddress:
    """Address that has been verified by external service."""
    street_line_1: str
    street_line_2: str | None
    city: str
    state: str
    postal_code: str
    country: str
    verification_id: str  # ID from verification service
```

### Domain Exception

Located at `domain/exceptions.py`:

```python
class AddressVerificationError(DomainError):
    """Raised when address verification fails."""
    def __init__(self, reason: str, field: str | None = None) -> None:
        self.reason = reason
        self.field = field
        super().__init__(f"Address verification failed: {reason}")
```

### Order Entity

The `Order` aggregate now includes a verified shipping address:

```python
@dataclass
class Order:
    id: UUID
    user_id: UUID
    items: list[OrderItem]
    shipping_address: VerifiedAddress  # Required verified address
    submitted_at: datetime | None
```

## Application Layer

### Port Interface

Located at `application/ports/address_verification.py`:

```python
class VerificationStatus(Enum):
    VERIFIED = "verified"         # Address is valid and deliverable
    CORRECTED = "corrected"       # Address was corrected/standardized
    UNDELIVERABLE = "undeliverable"  # Address cannot receive deliveries
    INVALID = "invalid"           # Address format is invalid
    SERVICE_UNAVAILABLE = "service_unavailable"  # External service down

@dataclass(frozen=True)
class AddressVerificationResult:
    status: VerificationStatus
    standardized_address: dict | None  # Standardized address fields
    verification_id: str | None        # Service-provided ID
    error_message: str | None          # Human-readable error
    field_errors: dict[str, str] | None  # Field-specific errors

class AddressVerificationPort(ABC):
    @abstractmethod
    def verify(
        self,
        street_line_1: str,
        street_line_2: str | None,
        city: str,
        state: str,
        postal_code: str,
        country: str,
    ) -> AddressVerificationResult:
        """Verify and standardize an address."""
        pass
```

### CartService Integration

The `CartService` orchestrates address verification during cart submission:

```python
class CartService:
    def __init__(
        self,
        uow: UnitOfWork,
        address_verification: AddressVerificationPort | None = None,
    ):
        self._uow = uow
        self._address_verification = address_verification

    def verify_address(
        self, address: UnverifiedAddress
    ) -> tuple[VerifiedAddress, AddressVerificationResult]:
        """Verify address without submitting cart."""
        # Calls port and returns verified address

    def submit_cart(
        self,
        user_context: UserContext,
        shipping_address: UnverifiedAddress,
    ) -> Order:
        """Submit cart with verified shipping address."""
        # Verifies address, creates order with verified address
```

## Infrastructure Layer

### Stub Adapter

Located at `infrastructure/django_app/address_verification.py`:

```python
class StubAddressVerificationAdapter(AddressVerificationPort):
    """Stub adapter for development and testing."""

    def verify(self, ...) -> AddressVerificationResult:
        # Test triggers for different scenarios:
        # - "invalid" in street_line_1 → INVALID status
        # - "undeliverable" in street_line_1 → UNDELIVERABLE status
        # - "unavailable" in street_line_1 → SERVICE_UNAVAILABLE
        # - Otherwise → VERIFIED with uppercased/standardized address
```

### Database Model

The `OrderModel` stores the shipping address as JSON:

```python
class OrderModel(models.Model):
    # ... existing fields ...
    shipping_address = models.JSONField(default=dict)
```

### Repository

The `DjangoOrderRepository` handles address serialization:

```python
def save(self, order: Order) -> Order:
    # Converts VerifiedAddress to JSON for storage

def _to_domain(self, model: OrderModel) -> Order:
    # Reconstructs VerifiedAddress from JSON
```

## API Endpoints

### Verify Address (Optional Pre-check)

**POST** `/api/cart/verify-address/`

Allows frontend to verify address before submission for better UX.

Request:
```json
{
  "street_line_1": "123 Main St",
  "street_line_2": "Apt 4",
  "city": "Anytown",
  "state": "CA",
  "postal_code": "90210",
  "country": "US"
}
```

Response (success):
```json
{
  "verified": true,
  "status": "verified",
  "standardized_address": {
    "street_line_1": "123 MAIN ST APT 4",
    "street_line_2": null,
    "city": "ANYTOWN",
    "state": "CA",
    "postal_code": "90210",
    "country": "US",
    "verification_id": "STUB-90210"
  }
}
```

Response (failure):
```json
{
  "verified": false,
  "status": "invalid",
  "error_message": "Invalid address format",
  "field_errors": {
    "street_line_1": "Street address is invalid"
  }
}
```

### Submit Cart

**POST** `/api/cart/submit/`

Now requires shipping address.

Request:
```json
{
  "shipping_address": {
    "street_line_1": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "postal_code": "90210",
    "country": "US"
  }
}
```

Response (success):
```json
{
  "order_id": "uuid",
  "message": "Order submitted successfully"
}
```

Response (invalid address):
```json
{
  "error": "Address verification failed: Invalid address format",
  "field": "street_line_1"
}
```

## Error Handling

| Scenario | HTTP Status | Response |
|----------|-------------|----------|
| Invalid address format | 400 | `{"error": "Address verification failed: ...", "field": "..."}` |
| Undeliverable address | 400 | `{"error": "Address verification failed: Address is not deliverable"}` |
| Service unavailable | 400 | `{"error": "Address verification failed: Service unavailable"}` |
| Missing shipping_address | 400 | `{"error": "shipping_address is required"}` |

## Design Decisions

### Why Stub Adapter Only?

This reference application demonstrates the pattern without requiring an external service account. The stub adapter:
- Validates the port/adapter architecture
- Enables full testing without network calls
- Shows how to handle different verification outcomes
- Can be replaced with a real adapter (USPS, SmartyStreets, etc.) in production

### Why Fail Closed?

Orders are rejected if address verification fails:
- Prevents undeliverable orders from being created
- Forces immediate resolution of address issues
- Simplifies order fulfillment downstream

### Why Separate Verify Endpoint?

The `/verify-address/` endpoint allows:
- Inline validation as user types
- Display of standardized address before submission
- Better UX by showing corrections early

### Why VerifiedAddress Value Object?

The `VerifiedAddress` type provides:
- Compile-time enforcement that orders have verified addresses
- Clear distinction between user input and verified data
- Immutable record of what was verified

## Testing

### Stub Adapter Test Cases

Use special values in `street_line_1` to trigger different responses:

| Input Contains | Result Status |
|----------------|---------------|
| "invalid" | INVALID |
| "undeliverable" | UNDELIVERABLE |
| "unavailable" | SERVICE_UNAVAILABLE |
| (normal address) | VERIFIED |

Example test:
```python
def test_invalid_address_fails():
    address = UnverifiedAddress(
        street_line_1="invalid address",
        city="Test", state="CA", postal_code="12345", country="US"
    )
    with pytest.raises(AddressVerificationError):
        cart_service.submit_cart(user_context, shipping_address=address)
```

## Future Enhancements

1. **Real adapter implementation** - HTTP client for USPS, SmartyStreets, etc.
2. **Address autocomplete** - Suggest addresses as user types
3. **International support** - Country-specific validation rules
4. **Address caching** - Cache verification results to reduce API calls
5. **Retry logic** - Retry transient failures with backoff
