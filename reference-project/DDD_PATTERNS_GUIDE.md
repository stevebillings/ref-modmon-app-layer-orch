# DDD Patterns Guide

This guide walks through the Domain-Driven Design patterns demonstrated in this reference project.

## Table of Contents

1. [Entities vs Value Objects](#entities-vs-value-objects)
2. [Aggregates and Invariants](#aggregates-and-invariants)
3. [Repository Pattern](#repository-pattern)
4. [Use Cases (Application Services)](#use-cases-application-services)
5. [Dependency Inversion](#dependency-inversion)
6. [Layered Architecture](#layered-architecture)

---

## Entities vs Value Objects

### Entity: Task

**Location**: `src/domain/entities/Task.ts`

Entities have:
- **Identity**: Unique ID that persists throughout lifecycle
- **Mutability**: State can change over time
- **Behavior**: Rich methods encapsulating business logic

```typescript
const task = Task.create('Implement feature', 'Description');
console.log(task.getId()); // Unique TaskId

task.startProgress(); // State changes
task.complete(email);  // More state changes
```

**Key characteristics**:
- Has a unique `TaskId`
- Equality based on ID, not attributes
- Contains business methods (not just getters/setters)

### Value Object: Email

**Location**: `src/domain/value-objects/Email.ts`

Value Objects have:
- **No identity**: Defined by their attributes
- **Immutability**: Cannot be changed after creation
- **Self-validation**: Validates on creation

```typescript
const email = Email.create('john@example.com');
// No setters - immutable
// Equality based on value
```

**Key characteristics**:
- No unique identifier
- Immutable (no setters)
- Self-validating (throws on invalid input)
- Equality based on all attributes

### When to Use Which?

**Use Entity when**:
- Object needs unique identity
- Object changes over time
- You need to track object through its lifecycle

**Use Value Object when**:
- Object is defined by its attributes
- Object is naturally immutable
- You want to avoid null reference issues

---

## Aggregates and Invariants

**Location**: `src/domain/entities/Task.ts`

An aggregate is a cluster of domain objects treated as a single unit. The `Task` class acts as an aggregate root.

### Enforcing Invariants

Invariants are business rules that must always be true. The aggregate root enforces these:

```typescript
class Task {
  // Invariant: Only assignee can complete task
  complete(completedByEmail: Email): void {
    if (this.assigneeEmail && !this.assigneeEmail.equals(completedByEmail)) {
      throw new Error('Only the assigned user can complete this task');
    }
    // ... complete task
  }

  // Invariant: Cannot modify completed tasks
  updateTitle(newTitle: string): void {
    this.ensureNotCompleted();
    this.setTitle(newTitle);
  }

  private ensureNotCompleted(): void {
    if (this.status.isCompleted()) {
      throw new Error('Cannot modify a completed task');
    }
  }
}
```

### Aggregate Boundaries

- External code can only access the aggregate through the root
- All changes go through aggregate root methods
- Aggregate root ensures all invariants are maintained
- Single transaction boundary

**Best practices**:
- Keep aggregates small
- One repository per aggregate
- Use IDs to reference other aggregates (not object references)

---

## Repository Pattern

**Interface**: `src/domain/repositories/ITaskRepository.ts`  
**Implementation**: `src/infrastructure/persistence/repositories/InMemoryTaskRepository.ts`

### Interface (Domain Layer)

The repository interface is defined in the domain layer but implemented in infrastructure:

```typescript
// Domain layer - defines WHAT we need
export interface ITaskRepository {
  findById(id: TaskId): Promise<Task | null>;
  findAll(): Promise<Task[]>;
  save(task: Task): Promise<void>;
  delete(id: TaskId): Promise<void>;
}
```

### Implementation (Infrastructure Layer)

```typescript
// Infrastructure layer - defines HOW we do it
export class InMemoryTaskRepository implements ITaskRepository {
  private tasks: Map<string, Task> = new Map();

  async findById(id: TaskId): Promise<Task | null> {
    return this.tasks.get(id.getValue()) || null;
  }
  // ... other methods
}
```

### Key Benefits

1. **Abstraction**: Domain doesn't know about database
2. **Testability**: Easy to swap with in-memory implementation
3. **Flexibility**: Can change database without changing domain
4. **Collection-like interface**: Works like a collection

### Testing with Repositories

```typescript
// Easy to test - no database needed
const repository = new InMemoryTaskRepository();
const useCase = new CreateTaskUseCase(repository);

await useCase.execute({ title: 'Test' });
expect(repository.count()).toBe(1);
```

---

## Use Cases (Application Services)

**Location**: `src/application/use-cases/`

Use cases orchestrate domain objects to fulfill application operations. They are thin layers that:

1. Accept DTOs
2. Create domain objects
3. Call domain methods
4. Persist changes
5. Return DTOs

### Example: CreateTaskUseCase

```typescript
export class CreateTaskUseCase {
  constructor(private readonly taskRepository: ITaskRepository) {}

  async execute(dto: CreateTaskDTO): Promise<TaskDTO> {
    // 1. Validate input
    if (!dto.title) throw new Error('Title is required');

    // 2. Create domain objects (value objects, entities)
    const assigneeEmail = dto.assigneeEmail 
      ? Email.create(dto.assigneeEmail)
      : null;

    // 3. Delegate to domain - business logic happens here
    const task = Task.create(dto.title, dto.description, assigneeEmail);

    // 4. Persist using repository
    await this.taskRepository.save(task);

    // 5. Return DTO (not domain object)
    return this.toDTO(task);
  }
}
```

### What Use Cases Should NOT Do

❌ Contain business logic (that's the domain's job)  
❌ Know about HTTP, databases, or frameworks  
❌ Return domain objects directly (use DTOs)  
❌ Be complicated (they orchestrate, not implement)

### What Use Cases SHOULD Do

✅ Validate input  
✅ Coordinate domain objects  
✅ Manage transactions  
✅ Convert between DTOs and domain objects  

---

## Dependency Inversion

The Dependency Inversion Principle states that high-level modules should not depend on low-level modules. Both should depend on abstractions.

### Traditional (Wrong) Approach

```typescript
// Domain depends on infrastructure - BAD!
import { PostgresTaskRepository } from '../infrastructure/...';

class Task {
  private repository = new PostgresTaskRepository(); // Domain knows about DB!
}
```

### DDD (Correct) Approach

```typescript
// Domain defines interface
export interface ITaskRepository {
  save(task: Task): Promise<void>;
}

// Infrastructure implements interface
export class InMemoryTaskRepository implements ITaskRepository {
  async save(task: Task): Promise<void> { /* ... */ }
}

// Application uses interface (injected)
export class CreateTaskUseCase {
  constructor(private repository: ITaskRepository) {} // Depends on abstraction
}
```

### Dependency Injection

In `src/index.ts`, we wire everything together:

```typescript
// Infrastructure layer
const taskRepository = new InMemoryTaskRepository();

// Application layer (injected with repository)
const createTaskUseCase = new CreateTaskUseCase(taskRepository);

// Presentation layer (injected with use case)
const taskController = new TaskController(createTaskUseCase, ...);
```

**Benefits**:
- Domain has zero dependencies
- Easy to test (inject mocks)
- Easy to swap implementations
- Clear dependency flow

---

## Layered Architecture

### Layer Responsibilities

```
┌─────────────────────────────────────────┐
│     Presentation (controllers, routes)  │ ← HTTP concerns
├─────────────────────────────────────────┤
│     Application (use cases, DTOs)       │ ← Orchestration
├─────────────────────────────────────────┤
│     Domain (entities, value objects)    │ ← Business logic
├─────────────────────────────────────────┤
│     Infrastructure (repositories, DB)   │ ← Technical details
└─────────────────────────────────────────┘
```

### Dependency Flow

Dependencies ALWAYS point inward:

```
Presentation → Application → Domain
       ↓
Infrastructure → Domain (through interfaces)
```

### Layer Details

#### Domain Layer (`src/domain/`)
- Pure business logic
- Zero dependencies on other layers
- Defines repository interfaces
- Contains entities, value objects, domain services

#### Application Layer (`src/application/`)
- Depends on domain layer only
- Orchestrates domain objects
- Contains use cases and DTOs
- Thin layer - delegates to domain

#### Infrastructure Layer (`src/infrastructure/`)
- Depends on domain layer (implements interfaces)
- Database access
- External services
- Framework-specific code

#### Presentation Layer (`src/presentation/`)
- Depends on application layer
- HTTP concerns (requests, responses)
- Input validation
- Error handling

### Cross-Cutting Concerns

Some things span multiple layers:
- **Logging**: Can be in any layer (with appropriate abstraction)
- **Authentication**: Middleware in presentation layer
- **Validation**: Input validation in presentation, business validation in domain
- **Error Handling**: Each layer handles its own errors appropriately

---

## Practical Examples

### Example 1: Adding a New Feature

**Requirement**: Add ability to assign priority to tasks

**Steps**:

1. **Domain Layer**: Add `Priority` value object
```typescript
// src/domain/value-objects/Priority.ts
export class Priority {
  static high(): Priority { /* ... */ }
  static medium(): Priority { /* ... */ }
  static low(): Priority { /* ... */ }
}
```

2. **Domain Layer**: Update `Task` entity
```typescript
class Task {
  private priority: Priority;
  
  setPriority(priority: Priority): void {
    this.priority = priority;
  }
}
```

3. **Application Layer**: Update DTOs
```typescript
interface CreateTaskDTO {
  title: string;
  priority?: string;
}
```

4. **Application Layer**: Update use cases
```typescript
const priority = dto.priority 
  ? Priority.fromString(dto.priority)
  : Priority.medium();
```

5. **Presentation Layer**: Update API
```typescript
router.put('/tasks/:id/priority', ...);
```

### Example 2: Changing Persistence

**Requirement**: Switch from in-memory to PostgreSQL

**Steps**:

1. Create new repository implementation:
```typescript
// src/infrastructure/persistence/repositories/PostgresTaskRepository.ts
export class PostgresTaskRepository implements ITaskRepository {
  async save(task: Task): Promise<void> {
    // PostgreSQL implementation
  }
}
```

2. Update dependency injection:
```typescript
// src/index.ts
const taskRepository = new PostgresTaskRepository(); // Changed this line only
```

**Note**: Domain and application layers remain unchanged!

---

## Summary

This reference project demonstrates:

✅ **Rich domain models** with behavior  
✅ **Value objects** for type safety and validation  
✅ **Aggregates** that enforce invariants  
✅ **Repository pattern** for persistence abstraction  
✅ **Use cases** for application orchestration  
✅ **Dependency inversion** for loose coupling  
✅ **Layered architecture** with clear boundaries  

The result is a codebase that is:
- **Maintainable**: Clear separation of concerns
- **Testable**: Easy to test each layer in isolation
- **Flexible**: Easy to change technical details
- **Understandable**: Code reflects business domain
