# Future Challenges/Solutions to Consider

This document tracks additional patterns and solutions typical of medium complexity web applications that we should consider added to this reference project.

## Completed

1. ~~**Domain Events**~~ - Implemented with sync/async handler support. See `features/DOMAIN-EVENTS-AND-AUDIT-LOGGING.md`.

2. ~~**Audit Logging**~~ - Implemented as a domain event subscriber. See `features/DOMAIN-EVENTS-AND-AUDIT-LOGGING.md`.

3. ~~**Authentication & Authorization**~~ - Django session auth with role-based access (admin can manage products, customers manage their own cart). Shows how auth concerns stay out of domain logic via UserContext pattern. See `features/AUTHENTICATION-AND-AUTHORIZATION.md`.

4. ~~**Pagination & Filtering**~~ - Implemented with search, price range filtering, stock availability filtering, and paginated results. See `features/PAGINATION-AND-FILTERING.md`.

## High Value Additions

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
