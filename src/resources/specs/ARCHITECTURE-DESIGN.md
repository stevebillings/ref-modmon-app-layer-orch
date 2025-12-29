# Architecture and design

This document specifies the architecture and design (primary data entities, backend APIs, etc.) for the project.

## Architecture

### Backend architecture

Architecture goals:
1. Separation of concerns
1. Fairly minimal dependence on the Django framework. We want to benefit from the way Django (like other modern framworks) makes it easy to receive a request and respond to it, but we don't want to over-rely on Django. In particular, we don't want to rely on Django capabilities that might not be provided by other frameworks (like Flask and FastAPI). We'll accomplish this by choosing to implement some things that Django might be able to do for us, and by using software patterns like the Repository Pattern.

The core business logic should have no dependencies on Django, and be clearly separate from the Django-dependent code (in its own directory).

The backend architecture should follow Domain Driven Design. We'll choose some simplifications noted below to reduce complexity.

The backend should use the Repository Pattern, and the Unit of Work Pattern, but rather than using events for eventual consistency across aggregates, the backend should achieve strong consistency across aggregate by using (a) a single database transaction per request that includes all database activity within that request, and (b) an application layer to orchistrate actions that span aggregates.

### Frontend architecture

Follow best practices for good separation of concerns in this type of application.

## Design

### Data entities

#### WorkoutStructure
- **id** (Primary Key)
- **interval_count** (integer) - Number of intervals in the workout
- **work_phase_meters** (integer) - Length of each work phase in meters (same for all intervals)
- **rest_phase_minutes** (float) - Duration of each rest phase in minutes (same for all intervals)
- **created_at** (timestamp)
- **Note**: Name is not stored. Backend generates a display name at read time (e.g., "5 x 500m / 2min rest") and includes it in API responses.

#### PerformedWorkout
- **id** (Primary Key)
- **workout_structure_id** (Foreign Key to WorkoutStructure)
- **performed_date** (date) - The date the workout was performed (user-entered)
- **created_at** (timestamp)

#### WorkoutInterval
- **id** (Primary Key)
- **performed_workout_id** (Foreign Key to PerformedWorkout)
- **interval_number** (integer) - The interval number (1, 2, 3, etc.)
- **time_seconds** (integer) - Total time for the work phase in seconds
- **Note**: Frontend handles conversion between seconds (for API/DB) and mm:ss format (for user display/entry)

### Backend APIs

#### WorkoutStructure Endpoints
- **GET /api/workout-structures/** - List all workout structures
  - Response: Array of WorkoutStructure objects (each includes generated `name` field for display)
- **POST /api/workout-structures/** - Create a new workout structure
  - Request body: `{ interval_count, work_phase_meters, rest_phase_minutes }`
  - Response: Created WorkoutStructure object (includes generated `name` field)
- **DELETE /api/workout-structures/{id}/** - Delete a workout structure
  - Response: 204 No Content

#### PerformedWorkout Endpoints
- **GET /api/performed-workouts/** - List all performed workouts
  - Response: Array of PerformedWorkout objects (includes nested workout_structure details and intervals with time in seconds)
- **POST /api/performed-workouts/** - Create a new performed workout
  - Request body: `{ workout_structure_id, performed_date, intervals: [{ interval_number, time_seconds }] }`
  - Response: Created PerformedWorkout object with intervals
- **DELETE /api/performed-workouts/{id}/** - Delete a performed workout
  - Response: 204 No Content

