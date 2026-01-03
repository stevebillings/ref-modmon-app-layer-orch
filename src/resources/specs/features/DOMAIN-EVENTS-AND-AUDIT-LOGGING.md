# Domain Events and Audit Logging Implementation

## Overview

This document describes the implementation of domain events and audit logging for the reference web application. Domain events enable loose coupling between aggregates and support cross-cutting concerns like audit logging without polluting domain logic.

## Architecture

### Event Flow

```
Aggregate Method Called (e.g., cart.add_item())
    ↓
Event Raised Internally (_raise_event())
    ↓
Application Service Saves Aggregate
    ↓
Application Service Collects Events (uow.collect_events_from())
    ↓
Transaction Commits
    ↓
Events Dispatched to Handlers (uow.dispatch_events())
    ↓
Audit Handler Writes to Database
```

### Key Design Decisions

1. **Internal Collection Pattern**: Aggregates maintain an internal `_domain_events` list. After operations, the application layer queries `get_domain_events()` to retrieve them. This keeps method signatures clean and naturally accumulates events across multiple operations.

2. **Actor ID**: Hardcoded as "anonymous" initially. When authentication is added, this will be replaced with the actual user ID.

3. **Sync/Async Handler Support**: The dispatcher supports both sync and async handlers:
   - **Sync handlers** (`register()`): Run immediately in the calling thread. Use for fast, critical handlers like audit logging.
   - **Async handlers** (`register_async()`): Run in a background thread pool. Use for slow handlers like sending emails or calling external APIs.

4. **Post-Commit Dispatch**: Events are only dispatched after the transaction commits successfully, ensuring consistency between database state and published events. Sync handlers run first, then async handlers are submitted to the thread pool.

5. **Resilient Handlers**: Handler failures are logged but don't break operations or prevent other handlers from running. The business transaction succeeds even if a handler fails.

## Domain Layer

### Base Event Class

Location: `backend/domain/events.py`

```python
@dataclass(frozen=True)
class DomainEvent:
    event_id: UUID
    occurred_at: datetime
```

All domain events are immutable value objects with a unique ID and timestamp.

### Event Types

#### Product Events (`backend/domain/aggregates/product/events.py`)
- `StockReserved` - Raised when stock is reserved for a cart item
- `StockReleased` - Raised when reserved stock is released

#### Cart Events (`backend/domain/aggregates/cart/events.py`)
- `CartItemAdded` - Raised when an item is added to cart
- `CartItemQuantityUpdated` - Raised when item quantity changes
- `CartItemRemoved` - Raised when an item is removed from cart
- `CartSubmitted` - Raised when cart is submitted as an order

#### Order Events (`backend/domain/aggregates/order/events.py`)
- `OrderCreated` - Raised when an order is created from a cart

### Aggregate Event Collection

Aggregates gain three methods:
- `_raise_event(event)` - Internal method to record an event
- `get_domain_events()` - Returns collected events (for application layer)
- `clear_domain_events()` - Clears events after dispatch

Methods that trigger business events (like `reserve_stock()`, `add_item()`) call `_raise_event()` internally.

## Infrastructure Layer

### Event Dispatcher

Location: `backend/infrastructure/events/dispatcher.py`

The `SyncEventDispatcher` supports both synchronous and asynchronous handlers:

```python
dispatcher = SyncEventDispatcher()

# Sync handler - runs immediately, blocks until complete
dispatcher.register(StockReserved, audit_log_handler)

# Async handler - runs in background thread pool
dispatcher.register_async(OrderCreated, send_confirmation_email)
```

Async handlers use a shared `ThreadPoolExecutor` with 4 worker threads. This provides non-blocking dispatch without requiring external infrastructure like message queues.

### Audit Log Model

Location: `backend/infrastructure/django_app/models.py`

```python
class AuditLogModel:
    event_type: str      # e.g., "StockReserved"
    event_id: UUID       # Unique event identifier
    occurred_at: datetime
    actor_id: str        # Who performed the action
    aggregate_type: str  # e.g., "Product", "Cart"
    aggregate_id: UUID   # The affected aggregate
    event_data: JSON     # Full event payload
```

### Unit of Work Integration

The `UnitOfWork` class is extended to:
1. Accept an optional event dispatcher
2. Collect events from aggregates via `collect_events_from(aggregate)`
3. Dispatch events after transaction commit via `dispatch_events()`

## Application Layer

### Service Changes

Application services call `uow.collect_events_from(aggregate)` after saving each modified aggregate. This extracts events from the aggregate and queues them for dispatch.

Example:
```python
def add_item(self, product_id: str, quantity: int) -> Cart:
    # ... business logic ...

    self.uow.get_cart_repository().save(cart)
    self.uow.get_product_repository().save(product)

    # Collect events from modified aggregates
    self.uow.collect_events_from(cart)
    self.uow.collect_events_from(product)

    return cart
```

## Testing Strategy

1. **Domain Event Tests**: Verify events are immutable and serialize correctly
2. **Aggregate Tests**: Verify aggregates raise correct events for each operation
3. **Integration Tests**: Verify full flow from operation to audit log entry

## Future Enhancements

1. **Authentication Integration**: Replace "anonymous" actor_id with real user IDs
2. **Message Queue**: For very high-volume scenarios or cross-service communication, replace thread pool with a message queue (e.g., Redis, RabbitMQ)
3. **Event Sourcing**: Use events as the source of truth (if needed)
4. **Additional Subscribers**: Notifications, analytics, external system sync
