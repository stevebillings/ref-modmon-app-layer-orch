# Domain-Driven Design (DDD) Web Application Architecture Specification

## Overview

This document specifies a simple-but-good architecture for web applications based on Domain-Driven Design (DDD) principles. The architecture promotes maintainability, testability, and clear separation of concerns.

## Core Principles

1. **Domain-Centric Design**: Business logic resides in the domain layer, independent of infrastructure concerns
2. **Separation of Concerns**: Clear boundaries between layers with well-defined responsibilities
3. **Dependency Rule**: Dependencies point inward - domain has no dependencies on outer layers
4. **Ubiquitous Language**: Code reflects the business domain language
5. **Encapsulation**: Domain entities protect their invariants

## Architecture Layers

### 1. Domain Layer (Core)

**Purpose**: Contains business logic, rules, and domain models

**Components**:
- **Entities**: Objects with unique identity that persist over time
- **Value Objects**: Immutable objects defined by their attributes
- **Aggregates**: Clusters of entities and value objects with a root entity
- **Domain Events**: Events representing significant business occurrences
- **Domain Services**: Operations that don't naturally belong to entities

**Characteristics**:
- Zero dependencies on infrastructure or application layers
- Pure business logic
- Framework-agnostic
- Highly testable

**Example Structure**:
```
domain/
  entities/
    User.ts
    Order.ts
  value-objects/
    Email.ts
    Money.ts
  aggregates/
    OrderAggregate.ts
  events/
    OrderPlaced.ts
  services/
    PricingService.ts
  repositories/ (interfaces only)
    IUserRepository.ts
```

### 2. Application Layer

**Purpose**: Orchestrates domain objects to fulfill use cases

**Components**:
- **Use Cases / Application Services**: Coordinate domain objects for specific operations
- **DTOs (Data Transfer Objects)**: Data structures for communication between layers
- **Mappers**: Convert between domain models and DTOs

**Characteristics**:
- Depends on domain layer
- No business logic (delegates to domain)
- Transaction management
- Thin orchestration layer

**Example Structure**:
```
application/
  use-cases/
    CreateOrderUseCase.ts
    GetUserUseCase.ts
  dtos/
    CreateOrderDTO.ts
    UserDTO.ts
  mappers/
    UserMapper.ts
```

### 3. Infrastructure Layer

**Purpose**: Implements technical capabilities and external integrations

**Components**:
- **Repositories (Implementations)**: Data persistence implementations
- **External Services**: Third-party API integrations
- **Persistence**: Database configurations and ORM setup
- **Messaging**: Event bus, message queue implementations

**Characteristics**:
- Implements interfaces defined in domain layer
- Framework-specific code
- Database access code
- External API clients

**Example Structure**:
```
infrastructure/
  persistence/
    repositories/
      UserRepositoryImpl.ts
    database/
      DatabaseConfig.ts
  external/
    PaymentGateway.ts
  messaging/
    EventBus.ts
```

### 4. Presentation Layer (API/UI)

**Purpose**: Handles user interactions and external requests

**Components**:
- **Controllers**: Handle HTTP requests and responses
- **Routes**: API endpoint definitions
- **Middleware**: Authentication, validation, error handling
- **View Models**: UI-specific data structures

**Characteristics**:
- Depends on application layer
- HTTP/REST concerns
- Input validation
- Response formatting

**Example Structure**:
```
presentation/
  controllers/
    UserController.ts
    OrderController.ts
  routes/
    api.ts
  middleware/
    AuthMiddleware.ts
    ValidationMiddleware.ts
```

## DDD Building Blocks

### Entities

**Definition**: Objects with unique identity and lifecycle

**Characteristics**:
- Has a unique identifier (ID)
- Mutable state
- Equality based on ID
- Contains behavior (not anemic)

**Example**:
```typescript
class User {
  constructor(
    private readonly id: UserId,
    private email: Email,
    private name: string
  ) {}

  changeEmail(newEmail: Email): void {
    // Business logic and validation
    this.email = newEmail;
  }

  getId(): UserId {
    return this.id;
  }
}
```

### Value Objects

**Definition**: Immutable objects defined by their attributes

**Characteristics**:
- No unique identity
- Immutable
- Equality based on all attributes
- Self-validating

**Example**:
```typescript
class Email {
  private constructor(private readonly value: string) {}

  static create(email: string): Email {
    if (!this.isValid(email)) {
      throw new Error('Invalid email format');
    }
    return new Email(email);
  }

  private static isValid(email: string): boolean {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  getValue(): string {
    return this.value;
  }
}
```

### Aggregates

**Definition**: Cluster of related objects treated as a unit

**Characteristics**:
- Has a root entity
- Enforces invariants
- Transactional boundary
- External references only to root

**Example**:
```typescript
class Order {
  private items: OrderItem[] = [];

  addItem(product: Product, quantity: number): void {
    // Enforce aggregate invariants
    if (this.items.length >= 10) {
      throw new Error('Order cannot have more than 10 items');
    }
    this.items.push(new OrderItem(product, quantity));
  }

  getTotalPrice(): Money {
    return this.items.reduce(
      (total, item) => total.add(item.getPrice()),
      Money.zero()
    );
  }
}
```

### Repositories

**Definition**: Abstractions for accessing and persisting aggregates

**Characteristics**:
- Interface defined in domain layer
- Implementation in infrastructure layer
- Collection-like interface
- Works with aggregate roots only

**Example**:
```typescript
// Domain layer - interface
interface IUserRepository {
  findById(id: UserId): Promise<User | null>;
  save(user: User): Promise<void>;
  delete(id: UserId): Promise<void>;
}

// Infrastructure layer - implementation
class UserRepositoryImpl implements IUserRepository {
  async findById(id: UserId): Promise<User | null> {
    // Database query implementation
  }
}
```

### Domain Services

**Definition**: Operations that don't naturally fit within entities

**Characteristics**:
- Stateless
- Named after domain activities
- Operates on multiple entities
- Contains domain logic

**Example**:
```typescript
class PricingService {
  calculateDiscount(order: Order, customer: Customer): Money {
    // Complex pricing logic involving multiple entities
  }
}
```

## Best Practices

### 1. Keep Entities Rich (Not Anemic)
- Put behavior in entities, not just data
- Validate invariants within entities
- Avoid public setters

### 2. Make Value Objects Immutable
- Create through factory methods
- Validate on creation
- No setters

### 3. Design Aggregates Carefully
- Keep aggregates small
- One repository per aggregate
- Use IDs to reference other aggregates

### 4. Use Domain Events
- Communicate between aggregates
- Decouple bounded contexts
- Enable event sourcing

### 5. Separate Commands and Queries (CQRS pattern - optional)
- Commands: Change state
- Queries: Read state
- Can use different models

### 6. Apply Layered Architecture Strictly
- Domain layer has no dependencies
- Application layer orchestrates only
- Infrastructure implements interfaces
- Presentation handles HTTP concerns

## Testing Strategy

### Unit Tests
- Test domain entities and value objects
- Test business logic in isolation
- Mock repository interfaces

### Integration Tests
- Test application layer use cases
- Test repository implementations
- Test with real database (or test containers)

### End-to-End Tests
- Test complete user workflows
- Test through presentation layer
- Test full stack integration

## Technology Recommendations

### Language
- TypeScript (type safety + JavaScript ecosystem)
- Or: C#, Java, Go (strongly typed languages)

### Framework
- Express.js or Fastify (lightweight, flexible)
- Or: NestJS (opinionated, DDD-friendly)

### Database
- PostgreSQL (relational, ACID compliance)
- Or: MongoDB (document store for certain domains)

### ORM
- TypeORM or Prisma (TypeScript-friendly)
- Keep ORM models separate from domain entities

### Testing
- Jest or Vitest (unit + integration)
- Supertest (API testing)

## Common Pitfalls to Avoid

1. **Anemic Domain Model**: Entities with only getters/setters
2. **Leaking Domain**: Domain objects in API responses
3. **Fat Repositories**: Business logic in repositories
4. **Tight Coupling**: Direct dependencies between layers
5. **Over-engineering**: Adding complexity without justification
6. **Ignoring Invariants**: Allowing invalid state in entities

## References

- Eric Evans: "Domain-Driven Design: Tackling Complexity in the Heart of Software"
- Vaughn Vernon: "Implementing Domain-Driven Design"
- Martin Fowler: Patterns of Enterprise Application Architecture
