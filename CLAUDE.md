# Reference web application

This is a reference web application. It's purpose is to demonstrate an architecture (focusing, at least for now, on the backend) for a medium complexity web application developed by a very small team (about 3 developers). The architecture that this project is demonstrating is a Domain Driven Design Modular Monolith that uses a thin application layer to orchestrate cross-aggregate operations.

The goal is to keep the application simple enough to be easy to understand, while still solving (demonstrating how to solve) a variety of problems typical of a medium complexity web application. For example: it includes solutions for:

1. Domain Driven Design Modular Monolith using Hexagonal architecture
2. Cross-aggregate operations
3. Domain events with sync/async handler support
4. Audit logging via domain event subscription

The specifications for the reference project are in src/resources/specs. These should always be considered, and as we change the application, we must also change the specs to keep them in sync.

Each time we prepare to introduce a new type of problem and its solution, we should consider changing or expanding the requirements and the application itself to make it better illustrate the problem and solution.
