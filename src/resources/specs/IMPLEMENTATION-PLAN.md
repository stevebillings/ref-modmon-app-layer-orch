# Implementation Plan

This document outlines the implementation plan for the workout tracking application.

## Phase 1: Project Setup

1. **Backend project initialization**
   - Create Django project structure with the specified directory layout (domain/, application/, infrastructure/)
   - Configure Django settings for development (SQLite database, CORS for local React dev server)
   - Install dependencies: Django, Django REST Framework, django-cors-headers, pytest, pytest-django

2. **Frontend project initialization**
   - Create React app with TypeScript using Vite
   - Set up directory structure (components/, pages/, services/, types/)
   - Install dependencies: React Router, Chakra UI, Jest + React Testing Library

## Phase 2: Backend Domain Layer (no Django dependencies)

3. **Domain entities**
   - `domain/aggregates/workout_structure/entity.py` - WorkoutStructure frozen dataclass with `generate_name()` method
   - `domain/aggregates/performed_workout/entities.py` - PerformedWorkout and WorkoutInterval frozen dataclasses

4. **Repository interfaces**
   - `domain/aggregates/workout_structure/repository.py` - Abstract base class defining CRUD operations
   - `domain/aggregates/performed_workout/repository.py` - Abstract base class defining CRUD operations

5. **Domain validation**
   - Validation logic for each entity (interval_count ranges, date constraints, etc.)
   - Custom domain exceptions (e.g., `DuplicateWorkoutStructureError`, `ValidationError`)

6. **Domain layer tests**
   - pytest tests for entity creation and validation
   - pytest tests for `generate_name()` formatting

## Phase 3: Backend Infrastructure Layer

7. **Django ORM models**
   - `infrastructure/django_app/models.py` - WorkoutStructure, PerformedWorkout, WorkoutInterval models
   - Unique constraint on WorkoutStructure (interval_count, work_phase_meters, rest_phase_minutes)
   - Cascade delete from WorkoutStructure to PerformedWorkout

8. **Repository implementations**
   - `infrastructure/django_app/repositories/workout_structure_repository.py` - Django ORM implementation
   - `infrastructure/django_app/repositories/performed_workout_repository.py` - Django ORM implementation
   - Mapping between ORM models and domain entities

9. **Unit of Work**
   - `infrastructure/django_app/unit_of_work.py` - Transaction management wrapper

10. **Utility functions**
    - `to_dict()` recursive conversion function for serializing domain entities

11. **Infrastructure layer tests**
    - pytest tests for repository implementations (using test database)
    - pytest tests for `to_dict()` conversion

## Phase 4: Backend Application Layer

12. **Application services**
    - `application/services/workout_structure_service.py` - Create, list, delete workout structures
    - `application/services/performed_workout_service.py` - Create, list, delete performed workouts (with interval count validation)

13. **Application layer tests**
    - pytest tests for application services with mocked repositories

## Phase 5: Backend API Layer

14. **Django views**
    - `infrastructure/django_app/views.py` - REST endpoints for all six API operations
    - Request parsing and response formatting using `to_dict()`

15. **URL routing**
    - Configure URL patterns for all endpoints

16. **Database migrations**
    - Generate and apply initial migrations

17. **API integration tests**
    - pytest tests for all endpoints (create, list, delete for both entities)
    - Tests for validation error responses
    - Tests for cascade delete behavior

## Phase 6: Frontend Foundation

18. **TypeScript types**
    - `types/` - WorkoutStructure, PerformedWorkout, WorkoutInterval interfaces matching API responses

19. **API service layer**
    - `services/api.ts` - Functions for all API calls (list, create, delete for both entities)

20. **Time utilities**
    - `services/timeUtils.ts` - Parse time string to seconds, format seconds to display string

21. **Frontend utility tests**
    - Jest tests for time parsing and formatting functions

## Phase 7: Frontend Components

22. **Shared components**
    - ConfirmationDialog - Chakra UI Modal wrapper for delete confirmations
    - ErrorAlert - Display API/validation errors

23. **WorkoutStructure components**
    - WorkoutStructureList - Display list with delete buttons
    - WorkoutStructureForm - Create form with validation

24. **PerformedWorkout components**
    - PerformedWorkoutList - Display list with delete buttons
    - PerformedWorkoutForm - Create form with structure dropdown, date picker, dynamic interval inputs

25. **Component tests**
    - Jest + React Testing Library tests for key component behaviors

## Phase 8: Frontend Pages

26. **Page components**
    - Landing page with navigation
    - Workout Structures page (list + create form)
    - Performed Workouts page (list + create form)

27. **Routing**
    - React Router configuration

28. **Page tests**
    - Jest tests for page rendering and navigation

## Phase 9: Integration & Polish

29. **End-to-end verification**
    - Manual verification of all flows: create/delete structures, create/delete workouts
    - Verify cascade delete behavior
    - Verify validation errors display correctly

30. **Empty states and error handling**
    - Implement empty state messages
    - Handle API errors gracefully

---

## Key Dependencies

- Phase 2 (domain) has no dependencies
- Phase 3 (infrastructure) depends on Phase 2
- Phase 4 (application) depends on Phases 2 & 3
- Phase 5 (API) depends on Phase 4
- Phase 6 (frontend types/services) can start after Phase 5 API design is clear
- Phases 7-8 (frontend UI) depend on Phase 6

## Technology Choices

- **Backend**: Python/Django, Django REST Framework, SQLite (dev), pytest
- **Frontend**: TypeScript, React, Vite, Chakra UI, Jest + React Testing Library
- **CSS Framework**: Chakra UI (React component library with built-in styling)
