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
│    REST API (using DRF)                                                      │
│    Adapters: Repositories (using Django ORM), EventDispatcher               │
│             UnitOfWork (using Django transactions)                           │
│                                       │ implements                           │
│    ┌──────────────────────────────────▼──────────────────────────────────┐  │
│    │    APPLICATION                                                       │  │
│    │    Services (orchestrate, authorize), Ports: UnitOfWork, Readers    │  │
│    │                                │                                     │  │
│    │    ┌───────────────────────────▼─────────────────────────────────┐  │  │
│    │    │    DOMAIN  (pure Python, no framework dependencies)         │  │  │
│    │    │                                                              │  │  │
│    │    │    ┌───────┐ ┌────┐ ┌─────┐ ┌──────┐                        │  │  │
│    │    │    │Product│ │Cart│ │Order│ │Coupon│  Aggregates            │  │  │
│    │    │    └───────┘ └────┘ └─────┘ └──────┘                        │  │  │
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
                                     └──────────┘
```

**How to read this diagram:**

The concentric boxes show the **Hexagonal (Ports & Adapters) Architecture**:
- **Domain** (innermost): Pure business logic with no external dependencies. Contains Aggregates (Product, Cart, Order, Coupon), Value Objects, Domain Events, and repository interfaces defined as abstract base classes.
- **Application**: Orchestrates use cases by coordinating aggregates. Defines additional port interfaces (UnitOfWork, Readers). Enforces authorization via UserContext.
- **Infrastructure** (outermost): Framework-dependent code. Django views handle HTTP. Adapters implement the port interfaces defined in inner layers.

**Dependency Rule**: Dependencies only point inward. Inner layers define interfaces (ports); outer layers provide implementations (adapters). This keeps the domain testable and framework-agnostic.

**Request Flow (command/write path)**: Frontend → REST API → Application Service → Aggregates → (saved via) Unit of Work → Database. Events dispatched after commit. Response converted via `to_dict()`.

This diagram shows the **command (write) path** in full — the one that goes through aggregates and enforces domain invariants. Complex reads take a different path entirely; see below.

## Query (Read) Path: Readers Bypass the Domain

Reports, dashboards, and any read that spans multiple aggregates (e.g. a product list annotated with total sold and currently reserved, pulled from Product, Order, and Cart tables) don't load and reconstruct aggregates — that would violate aggregate isolation, since no single aggregate owns that combined view. Instead they go through a **Reader**, a separate port defined in the Application layer (not Domain — a cross-aggregate read has no single aggregate to belong to) that talks to the database directly:

```
┌────────────────────────┐    ┌────────────────────────────────┐    ┌──────────┐
│ APPLICATION            │    │ INFRASTRUCTURE                 │    │          │
│                        │    │                                │    │          │
│ Reader Port (ABC)      │──▶ │ Reader Adapter                 │──▶ │ Database │
│ e.g. ProductReport-    │    │ e.g. DjangoProductReport-      │    │          │
│ Reader                 │    │ Reader (Django ORM,            │    │          │
│                        │    │ joins across tables/           │    │          │
│ Query dataclasses      │    │ aggregates freely)             │    │          │
│ (input/output DTOs)    │    │                                │    │          │
└────────────────────────┘    └────────────────────────────────┘    └──────────┘
```

An Application Service (e.g. `ProductReportService`) still sits in front of the Reader to apply authorization, exactly as it does for the command path — it just delegates straight to the Reader instead of loading an aggregate.

**Request Flow (query/read path)**: Frontend → REST API → Application Service (authorize) → Reader Port → Reader Adapter → Database, returning read-only DTOs. No aggregates, no Unit of Work, no domain events — reads don't mutate state, so there's nothing to make transactionally consistent or to raise events about.

## Key Patterns

| Pattern | Purpose | Location |
|---------|---------|----------|
| **Aggregate** | Consistency boundary with behavior | Domain layer |
| **Repository** | Abstract persistence interface for one aggregate | Port in Domain, Adapter in Infrastructure |
| **Reader** | Read-optimized query, may span multiple aggregates | Port in Application, Adapter in Infrastructure |
| **Unit of Work** | Transaction boundary, event collection | Port in Application, Adapter in Infrastructure |
| **Application Service** | Use case orchestration, cross-aggregate coordination, authorization | Application layer |
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
│       ├── order/              # Order aggregate + OrderItem VO
│       └── coupon/             # Coupon aggregate + repository ABC
│
├── application/                # Middle layer - orchestration
│   ├── services/               # Application services
│   ├── ports/                  # Port interfaces (UoW, Readers - e.g. ProductReportReader)
│   └── queries/                # Query dataclasses for readers (input/output DTOs)
│
└── infrastructure/             # Outermost - Django-dependent adapters
    ├── events/                 # Event dispatcher implementation
    └── django_app/
        ├── views.py            # REST API endpoints
        ├── repositories/       # Repository adapters (Django ORM) - write path
        ├── readers/            # Reader adapters (direct ORM, cross-aggregate) - read path
        └── unit_of_work.py     # UoW adapter with event dispatch
```
