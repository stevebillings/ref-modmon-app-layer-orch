# DDD Task Management - Reference Implementation

This is a reference implementation of a Domain-Driven Design (DDD) architecture for a simple task management application.

## Overview

This project demonstrates DDD principles and patterns through a practical example:
- **Domain**: Task management with tasks, users, and projects
- **Architecture**: Clean layered architecture following DDD patterns
- **Language**: TypeScript for type safety and modern JavaScript features

## Architecture

The application follows a strict layered architecture:

```
src/
├── domain/              # Core business logic (no dependencies)
│   ├── entities/        # Domain entities with identity
│   ├── value-objects/   # Immutable value objects
│   ├── repositories/    # Repository interfaces
│   └── services/        # Domain services
├── application/         # Use cases and orchestration
│   ├── use-cases/       # Application services
│   └── dtos/            # Data Transfer Objects
├── infrastructure/      # Technical implementations
│   └── persistence/     # Repository implementations
└── presentation/        # HTTP API layer
    ├── controllers/     # Request handlers
    └── routes/          # Route definitions
```

## Key DDD Concepts Demonstrated

### 1. Entities
- `Task`: Entity with unique identity and lifecycle
- Rich behavior, not anemic data containers
- Encapsulates business rules

### 2. Value Objects
- `TaskId`: Unique identifier
- `Email`: Self-validating email address
- `TaskStatus`: Type-safe status enumeration
- Immutable and self-validating

### 3. Aggregates
- `Task` acts as an aggregate root
- Enforces invariants (e.g., only owner can complete tasks)
- Transactional boundary

### 4. Repositories
- `ITaskRepository`: Interface in domain layer
- `InMemoryTaskRepository`: Implementation in infrastructure layer
- Abstracts persistence concerns

### 5. Domain Services
- Services for operations spanning multiple entities
- Stateless domain logic

### 6. Application Services (Use Cases)
- `CreateTaskUseCase`: Orchestrates task creation
- `CompleteTaskUseCase`: Orchestrates task completion
- Thin layer delegating to domain

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

```bash
npm install
```

### Running the Application

```bash
# Development mode
npm run dev

# Build
npm run build

# Production
npm start
```

### Running Tests

```bash
# Run all tests
npm test

# Watch mode
npm run test:watch
```

## API Endpoints

### Create Task
```bash
POST /api/tasks
Content-Type: application/json

{
  "title": "Implement user authentication",
  "description": "Add JWT-based authentication",
  "assigneeEmail": "john@example.com"
}
```

### Get Task
```bash
GET /api/tasks/:id
```

### Complete Task
```bash
POST /api/tasks/:id/complete
Content-Type: application/json

{
  "completedByEmail": "john@example.com"
}
```

### List Tasks
```bash
GET /api/tasks
```

## Project Structure Details

### Domain Layer (`src/domain/`)
Pure business logic with no external dependencies:
- **Entities**: Objects with identity (`Task`)
- **Value Objects**: Immutable values (`TaskId`, `Email`, `TaskStatus`)
- **Repository Interfaces**: Contracts for data access
- **Domain Services**: Business operations that don't fit in entities

### Application Layer (`src/application/`)
Orchestrates domain objects to fulfill use cases:
- **Use Cases**: Application-specific operations
- **DTOs**: Data structures for communication between layers

### Infrastructure Layer (`src/infrastructure/`)
Technical implementations:
- **Repository Implementations**: In-memory or database persistence
- **External Service Integrations**: APIs, messaging, etc.

### Presentation Layer (`src/presentation/`)
HTTP/API concerns:
- **Controllers**: Handle requests, call use cases, format responses
- **Routes**: API endpoint definitions
- **Middleware**: Authentication, validation, error handling

## Design Principles Applied

1. **Dependency Rule**: Dependencies point inward (domain → application → infrastructure/presentation)
2. **Single Responsibility**: Each class has one reason to change
3. **Encapsulation**: Domain entities protect their invariants
4. **Immutability**: Value objects are immutable
5. **Separation of Concerns**: Clear boundaries between layers

## Testing Strategy

- **Unit Tests**: Test domain entities and value objects in isolation
- **Integration Tests**: Test use cases with real repository implementations
- **API Tests**: Test HTTP endpoints end-to-end

## Learning Resources

- See `ARCHITECTURE_SPEC.md` for detailed architecture documentation
- Review domain entities for examples of rich domain models
- Check use cases for proper orchestration patterns
- Examine repositories for abstraction patterns

## License

MIT
