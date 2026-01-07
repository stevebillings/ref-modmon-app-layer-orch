# Glossary (Ubiquitous Language)

This document defines the ubiquitous language for the project. These terms should be used consistently in code, documentation, and conversation. When discussing the domain, use these exact terms to avoid ambiguity.

## E-Commerce Domain Terms

### Product
An item available for sale. Has a name, price, and stock quantity. Products can be soft-deleted (hidden from catalog but preserved in order history).

### Stock / Stock Quantity
The number of units of a product available for purchase. Stock is reduced when items are added to carts (reserved) and increased when items are removed (released).

### Reserve Stock
The act of decrementing a product's stock quantity when a customer adds it to their cart. This ensures stock is not oversold.

### Release Stock
The act of incrementing a product's stock quantity when a customer removes an item from their cart or when an order is cancelled. Returns previously reserved stock to availability.

### Cart
A user's temporary collection of items they intend to purchase. Each user has exactly one cart (singleton per user). Carts are mutable and can be modified until submitted.

### Cart Item
An entry in a cart representing a product the user intends to buy. Contains a snapshot of the product's name and price at the time of addition, plus the desired quantity.

### Quantity
The number of units of a product in a cart item or order item. Must be a positive integer.

### Order
An immutable record of a completed purchase. Created when a cart is submitted. Contains verified shipping address and snapshots of all items at time of purchase.

### Order Item
An entry in a submitted order. Contains a snapshot of the product's name and price at the time the order was placed, ensuring order history remains accurate even if products change or are deleted.

### Shipping Address
The destination for order delivery. Must be verified by an external service before an order can be submitted.

### Submit Cart / Submit Order
The act of converting a cart into an immutable order. Requires a verified shipping address. Clears the cart after successful submission.

### Soft Delete
Marking a product as deleted without removing it from the database. Soft-deleted products are hidden from the catalog but preserved for order history integrity.

### Restore
Reversing a soft delete, making a previously deleted product visible in the catalog again.

## Aggregate & Entity Terms

### Aggregate
A cluster of domain objects treated as a single unit for data changes. Each aggregate has a root entity and enforces its own consistency rules. The three aggregates in this system are Product, Cart, and Order.

### Aggregate Root
The primary entity of an aggregate that controls access to all objects within the aggregate boundary. External objects can only reference the aggregate through its root.

### Value Object
An immutable object defined by its attributes rather than identity. Examples: CartItem, OrderItem, VerifiedAddress. Value objects have no independent lifecycle.

### Snapshot
A copy of data from another aggregate captured at a point in time. Cart items and order items snapshot product names and prices to maintain historical accuracy.

## Address Terms

### Unverified Address
User-provided address input before validation. Contains street, city, state, postal code, and country. Cannot be used for order submission.

### Verified Address
An address that has been validated by an external verification service. Contains all fields from UnverifiedAddress plus a verification_id proving it was validated.

### Address Verification
The process of validating a shipping address through an external service. Required before cart submission. Uses fail-closed behavior (rejects unverifiable addresses).

## User & Authorization Terms

### Role
A user's access level in the system. Two roles exist: Admin and Customer.

### Admin
A user role with elevated privileges. Can create/delete products, restore deleted products, and view all orders.

### Customer
A standard user role. Can browse products, manage their own cart, and view their own order history.

### Capability
A specific action a user is permitted to perform, derived from their role. Examples: `products:create`, `products:delete`, `cart:modify`. Used by the frontend to show/hide UI elements.

### UserContext
A framework-agnostic representation of the authenticated user. Contains user ID, username, role, and capabilities. Passed to application services for authorization checks.

### Actor ID
An identifier for who performed an action, used in domain events for audit logging. Derived from UserContext.

## Architecture Terms

### Repository
An interface for persisting and retrieving aggregates. One repository per aggregate root. Defined in the domain layer, implemented in infrastructure.

### Application Service
A thin orchestration layer that coordinates use cases across aggregates. Handles authorization, transaction management, and cross-aggregate operations.

### Unit of Work
A transaction manager that ensures all database operations within a use case succeed or fail together. Also responsible for collecting and dispatching domain events.

### Domain Event
An immutable record of something significant that happened in the domain. Examples: StockReserved, CartItemAdded, OrderCreated. Used for audit logging and cross-cutting concerns.

### Port
An abstract interface defined in the application layer for external dependencies (address verification, email, feature flags).

### Adapter
A concrete implementation of a port that connects to external systems or frameworks. Examples: DjangoProductRepository, StubAddressVerificationAdapter.

### Cross-Aggregate Operation
An action that requires coordinating changes across multiple aggregates within a single transaction. Examples: adding an item to cart (updates Cart and Product), submitting cart (creates Order from Cart).

## Event Terms

### StockReserved
Domain event raised when stock is reserved for a cart item.

### StockReleased
Domain event raised when stock is released back to availability.

### CartItemAdded
Domain event raised when an item is added to a cart.

### CartItemQuantityUpdated
Domain event raised when a cart item's quantity is changed.

### CartItemRemoved
Domain event raised when an item is removed from a cart.

### CartSubmitted
Domain event raised when a cart is converted to an order.

### OrderCreated
Domain event raised when a new order is persisted.

### ProductDeleted
Domain event raised when a product is soft-deleted.

### ProductRestored
Domain event raised when a soft-deleted product is restored.

## Infrastructure Terms

### Feature Flag
A runtime toggle that enables or disables functionality without code deployment. Stored in the database, managed by admins.

### Audit Log
A persistent record of domain events for compliance and debugging. Automatically populated by an event handler.
