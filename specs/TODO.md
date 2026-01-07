# Future Challenges/Solutions to Consider

This document tracks additional patterns and solutions typical of medium complexity web applications that we should consider added to this reference project.

## Completed

1. ~~**Domain Events**~~ - Implemented with sync/async handler support. See `features/DOMAIN-EVENTS-AND-AUDIT-LOGGING.md`.

1. ~~**Audit Logging**~~ - Implemented as a domain event subscriber. See `features/DOMAIN-EVENTS-AND-AUDIT-LOGGING.md`.

1. ~~**Authentication & Authorization**~~ - Django session auth with role-based access (admin can manage products, customers manage their own cart). Shows how auth concerns stay out of domain logic via UserContext pattern. See `features/AUTHENTICATION-AND-AUTHORIZATION.md`.

1. ~~**Pagination & Filtering**~~ - Implemented with search, price range filtering, stock availability filtering, and paginated results. See `features/PAGINATION-AND-FILTERING.md`.

1. ~~**Soft Deletes**~~ - Products can be soft-deleted (hidden from catalog) while preserving order history. Includes restore functionality. See `features/SOFT-DELETE.md`.

1. ~~**Feature Flags**~~ - Toggle new features without deployment. See `features/FEATURE-FLAGS-AND-INCIDENT-NOTIFICATION.md`.

## High Value Additions

## Medium Value Additions

1. **Idempotency Keys** - Make order submission safe to retry. Important for any operation with side effects.

1. **Scheduled Jobs / Background Tasks** - e.g., "Expire unpurchased cart reservations after 30 minutes." Shows async patterns without full event sourcing.

1. **API Versioning** - How to evolve endpoints without breaking clients.

1. **Rate Limiting** - Protect against abuse, especially on write operations.

1. **Optimistic Locking** - Alternative to pessimistic locking for lower-contention scenarios. Could show both patterns side-by-side.

## Nice to Have

1. **Multi-tenancy** - If relevant to your target audience.

1. **File Uploads** - Product images, for example.

## Observability and Monitoring

1. ~~**Health check endpoint**~~ - Simple `/health` that checks DB connectivity. Essential for any deployment (k8s, load balancers). Implemented at `/api/health/`.

1. **Structured logging** - Consistent JSON format makes logs searchable. Useful even locally, essential in production.

1. **Request logging middleware** - Log request/response timing, status codes, user ID. Helps debug issues without full tracing infrastructure.

1. **Basic metrics endpoint** - Expose counts like requests, errors, maybe domain metrics (orders placed, carts submitted). Could use Prometheus format for compatibility.

1. **Correlate domain events with request IDs** - Associate domain events with the HTTP request that triggered them for end-to-end traceability.

1. **Time cross-aggregate operations** - Measure and expose timing for operations that span aggregates to show where complexity lives.
