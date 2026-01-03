# Hexagonal Architecture Violation: UnitOfWork Dependency

## The Problem

In `cart_service.py` (application layer), there is a direct dependency on `infrastructure.django_app.unit_of_work.UnitOfWork`, which has a dependency on `django.db.transaction`. This is a violation of hexagonal architecture principles.

## Why This Violates Hexagonal Architecture

In proper hexagonal architecture:

1. **Domain layer** - Pure business logic, no external dependencies
2. **Application layer** - Orchestrates use cases, depends only on abstractions (ports)
3. **Infrastructure layer** - Implements the abstractions (adapters)

The dependency rule is that inner layers should never depend on outer layers. When `cart_service.py` imports `UnitOfWork` directly from `infrastructure.django_app`, the application layer is depending on a concrete infrastructure implementation rather than an abstraction.

## The Correct Approach

1. Define a `UnitOfWork` abstract base class (a "port") in the domain or application layer - something like `domain/ports/unit_of_work.py` or `application/ports/unit_of_work.py`

2. Have the Django-specific implementation in infrastructure implement that abstraction

3. Inject the concrete implementation at runtime (via dependency injection at the composition root - typically in the web framework's configuration/startup)

This way:
- `cart_service.py` imports from `application.ports.unit_of_work.UnitOfWork` (an ABC)
- `infrastructure.django_app.unit_of_work.DjangoUnitOfWork` implements that ABC
- The wiring happens at the entry point (views/API handlers)

## Tradeoffs

This adds indirection and more files. For a small team, one might consciously decide the pragmatic violation is acceptable to reduce boilerplate. But if the goal is to demonstrate proper hexagonal architecture as a reference, then this should be fixed.
