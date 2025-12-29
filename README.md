# Web Application Architecture - DDD Reference

This repository provides specifications and a reference implementation for a simple-but-good Domain-Driven Design (DDD) web application architecture.

## Contents

1. **[ARCHITECTURE_SPEC.md](./ARCHITECTURE_SPEC.md)** - Comprehensive specification documenting DDD principles, patterns, and best practices
2. **[reference-project/](./reference-project/)** - Working reference implementation demonstrating the architecture

## What's Inside

### Architecture Specification

The specification document covers:
- **Core DDD Principles**: Domain-centric design, separation of concerns, dependency rules
- **Architecture Layers**: Domain, Application, Infrastructure, and Presentation layers
- **DDD Building Blocks**: Entities, Value Objects, Aggregates, Repositories, Domain Services
- **Best Practices**: Design patterns, testing strategies, and common pitfalls to avoid
- **Technology Recommendations**: Suggested tools and frameworks

### Reference Project

A fully functional task management application built with TypeScript that demonstrates:
- **Clean Architecture**: Strict layered architecture with proper dependency flow
- **Rich Domain Model**: Entities with behavior, not anemic data containers
- **Value Objects**: Immutable, self-validating objects
- **Repository Pattern**: Abstraction over data access
- **Use Cases**: Application services orchestrating domain logic
- **Comprehensive Tests**: Unit and integration tests demonstrating patterns

## Key Features

✅ **Simple but Complete**: Not oversimplified, but not over-engineered  
✅ **Production-Ready Patterns**: Real-world applicable architecture  
✅ **Well-Documented**: Extensive inline documentation and comments  
✅ **Fully Tested**: Demonstrates testing at each layer  
✅ **Type-Safe**: TypeScript for compile-time safety  
✅ **Framework-Agnostic Domain**: Core business logic has zero dependencies

## Getting Started

### Review the Specification
Start by reading [ARCHITECTURE_SPEC.md](./ARCHITECTURE_SPEC.md) to understand the architectural principles and patterns.

### Run the Reference Project
```bash
cd reference-project
npm install
npm test           # Run tests
npm run dev        # Start development server
```

### Explore the Code
Navigate through the layers:
```
reference-project/src/
├── domain/              # Pure business logic
├── application/         # Use cases / orchestration
├── infrastructure/      # Technical implementations
└── presentation/        # HTTP API layer
```

## Use Cases

This architecture is ideal for:
- Medium to large web applications
- Applications with complex business logic
- Projects requiring long-term maintainability
- Teams wanting clear separation of concerns
- Systems that may evolve significantly over time

## Learning Path

1. **Read** the architecture specification
2. **Explore** the domain layer (entities and value objects)
3. **Understand** the repository pattern (interface vs implementation)
4. **Review** the use cases in the application layer
5. **See** how it all wires together in `src/index.ts`
6. **Run** the tests to see patterns in action

## Architecture Highlights

### Dependency Rule
Dependencies flow inward: Presentation → Application → Domain

```
┌─────────────────────────────────────┐
│      Presentation Layer (API)       │
│  ┌───────────────────────────────┐  │
│  │    Application Layer (Use     │  │
│  │ ┌─────────────────────────┐   │  │
│  │ │   Domain Layer (Core)   │   │  │
│  │ │  - Entities             │   │  │
│  │ │  - Value Objects        │   │  │
│  │ │  - Business Rules       │   │  │
│  │ └─────────────────────────┘   │  │
│  │    Cases/Orchestration)       │  │
│  └───────────────────────────────┘  │
│         Controllers/Routes)         │
└─────────────────────────────────────┘
         Infrastructure Layer
       (Repository Implementations)
```

### Core Principles Demonstrated

- **Ubiquitous Language**: Code reflects business domain
- **Encapsulation**: Entities protect their invariants
- **Immutability**: Value objects cannot be changed after creation
- **Single Responsibility**: Each class has one reason to change
- **Testability**: Business logic testable without infrastructure

## Contributing

This is a reference architecture. Feel free to:
- Use it as a starting point for your projects
- Adapt it to your specific needs
- Share feedback and improvements

## License

MIT

## Resources

- Eric Evans: "Domain-Driven Design: Tackling Complexity in the Heart of Software"
- Vaughn Vernon: "Implementing Domain-Driven Design"
- Martin Fowler: Patterns of Enterprise Application Architecture