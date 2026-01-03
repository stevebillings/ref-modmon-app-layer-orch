# Future Challenges/Solutions to Demonstrate

This document tracks additional patterns and solutions typical of medium complexity web applications that should be added to this reference project.

## High Value Additions

1. **Domain Events** - Decouple aggregates further. When an order is submitted, publish an `OrderSubmittedEvent` that other modules can react to (e.g., notifications, analytics). Demonstrates the pattern without requiring a message broker.

2. **Authentication & Authorization** - Role-based access (e.g., admin can manage products, customers can only manage their own cart). Shows how auth concerns stay out of domain logic.

3. **Pagination & Filtering** - Product catalog search, filtering by price range, paginated results. Common requirement that touches all layers.

4. **Audit Logging** - Track who changed what and when. Demonstrates cross-cutting concerns without polluting domain logic.

5. **Soft Deletes** - Products shouldn't disappear from order history. Shows how to handle data retention while maintaining referential integrity.

## Medium Value Additions

6. **Idempotency Keys** - Make order submission safe to retry. Important for any operation with side effects.

7. **Scheduled Jobs / Background Tasks** - e.g., "Expire unpurchased cart reservations after 30 minutes." Shows async patterns without full event sourcing.

8. **API Versioning** - How to evolve endpoints without breaking clients.

9. **Rate Limiting** - Protect against abuse, especially on write operations.

10. **Optimistic Locking** - Alternative to pessimistic locking for lower-contention scenarios. Could show both patterns side-by-side.

## Nice to Have

11. **Feature Flags** - Toggle new features without deployment.

12. **Multi-tenancy** - If relevant to your target audience.

13. **File Uploads** - Product images, for example.
