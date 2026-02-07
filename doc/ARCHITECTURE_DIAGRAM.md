# Architecture Diagram

## System Overview: Hexagonal Architecture with DDD

```
                                     ┌──────────┐
                                     │ Frontend │
                                     │  (React) │
                                     └────┬─────┘
                                          │ HTTP/JSON
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│    INFRASTRUCTURE                                                            │
│    REST API, Adapters: Repositories, UnitOfWork, EventDispatcher            │
│                                       │ implements                           │
│    ┌──────────────────────────────────▼──────────────────────────────────┐  │
│    │    APPLICATION                                                       │  │
│    │    Services (orchestrate, authorize), Ports: UnitOfWork, Readers    │  │
│    │                                │                                     │  │
│    │    ┌───────────────────────────▼─────────────────────────────────┐  │  │
│    │    │    DOMAIN  (pure Python, no framework dependencies)         │  │  │
│    │    │                                                              │  │  │
│    │    │    ┌─────────┐   ┌─────────┐   ┌─────────┐                  │  │  │
│    │    │    │ Product │   │  Cart   │   │  Order  │  Aggregates      │  │  │
│    │    │    └─────────┘   └─────────┘   └─────────┘                  │  │  │
│    │    │                                                              │  │  │
│    │    │    Repository Interfaces (ABCs)  •  Domain Events           │  │  │
│    │    │                                                              │  │  │
│    │    └─────────────────────────────────────────────────────────────┘  │  │
│    │                                                                      │  │
│    └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
                                     ┌──────────┐
                                     │ Database │
                                     │ (SQLite) │
                                     └──────────┘
```

**How to read this diagram:**

The concentric boxes show the **Hexagonal (Ports & Adapters) Architecture**:
- **Domain** (innermost): Pure business logic with no external dependencies. Contains Aggregates (Product, Cart, Order), Value Objects, Domain Events, and repository interfaces defined as abstract base classes.
- **Application**: Orchestrates use cases by coordinating aggregates. Defines additional port interfaces (UnitOfWork, Readers). Enforces authorization via UserContext.
- **Infrastructure** (outermost): Framework-dependent code. Django views handle HTTP. Adapters implement the port interfaces defined in inner layers.

**Dependency Rule**: Dependencies only point inward. Inner layers define interfaces (ports); outer layers provide implementations (adapters). This keeps the domain testable and framework-agnostic.

**Request Flow**: Frontend → REST API → Application Service → Aggregates → (saved via) Unit of Work → Database. Events dispatched after commit. Response converted via `to_dict()`.

## Key Patterns

| Pattern | Purpose | Location |
|---------|---------|----------|
| **Aggregate** | Consistency boundary with behavior | Domain layer |
| **Repository** | Abstract persistence interface | Port in Domain, Adapter in Infrastructure |
| **Unit of Work** | Transaction boundary, event collection | Port in Application, Adapter in Infrastructure |
| **Application Service** | Use case orchestration, cross-aggregate coordination | Application layer |
| **Domain Event** | Decouple side effects (audit, notifications) | Raised in Domain, dispatched by Infrastructure |

## Directory Structure

```
backend/
├── domain/                     # Innermost - NO Django dependencies
│   ├── events.py               # Base DomainEvent class
│   ├── exceptions.py           # Domain errors
│   └── aggregates/
│       ├── product/            # Product aggregate + repository ABC
│       ├── cart/               # Cart aggregate + CartItem VO
│       └── order/              # Order aggregate + OrderItem VO
│
├── application/                # Middle layer - orchestration
│   ├── services/               # Application services
│   ├── ports/                  # Port interfaces (UoW, Readers)
│   └── queries/                # Query definitions for readers
│
└── infrastructure/             # Outermost - Django-dependent adapters
    ├── events/                 # Event dispatcher implementation
    └── django_app/
        ├── views.py            # REST API endpoints
        ├── repositories/       # Repository adapters (Django ORM)
        ├── readers/            # Query adapters (direct SQL/ORM)
        └── unit_of_work.py     # UoW adapter with event dispatch
```
