# API Examples

This document provides practical examples of using the Task Management API.

## Prerequisites

Start the server:
```bash
npm run dev
```

The server will run on `http://localhost:3000`

## Examples

### 1. Health Check

Check if the server is running:

```bash
curl http://localhost:3000/health
```

Response:
```json
{
  "status": "ok",
  "timestamp": "2025-12-29T22:48:32.489Z"
}
```

### 2. Create a Task

Create a new task with an assignee:

```bash
curl -X POST http://localhost:3000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement user authentication",
    "description": "Add JWT-based authentication",
    "assigneeEmail": "john@example.com"
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "id": "befde0c6-6955-4732-927b-b6502abe23b3",
    "title": "Implement user authentication",
    "description": "Add JWT-based authentication",
    "status": "TODO",
    "assigneeEmail": "john@example.com",
    "createdAt": "2025-12-29T22:48:32.696Z",
    "updatedAt": "2025-12-29T22:48:32.696Z",
    "completedAt": null
  }
}
```

Create a task without an assignee:

```bash
curl -X POST http://localhost:3000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Write documentation",
    "description": "Document the API endpoints"
  }'
```

### 3. Get a Task by ID

```bash
curl http://localhost:3000/api/tasks/befde0c6-6955-4732-927b-b6502abe23b3
```

Response:
```json
{
  "success": true,
  "data": {
    "id": "befde0c6-6955-4732-927b-b6502abe23b3",
    "title": "Implement user authentication",
    "description": "Add JWT-based authentication",
    "status": "TODO",
    "assigneeEmail": "john@example.com",
    "createdAt": "2025-12-29T22:48:32.696Z",
    "updatedAt": "2025-12-29T22:48:32.696Z",
    "completedAt": null
  }
}
```

### 4. List All Tasks

```bash
curl http://localhost:3000/api/tasks
```

Response:
```json
{
  "success": true,
  "data": [
    {
      "id": "befde0c6-6955-4732-927b-b6502abe23b3",
      "title": "Implement user authentication",
      "description": "Add JWT-based authentication",
      "status": "TODO",
      "assigneeEmail": "john@example.com",
      "createdAt": "2025-12-29T22:48:32.696Z",
      "updatedAt": "2025-12-29T22:48:32.696Z",
      "completedAt": null
    },
    {
      "id": "48ea1ae4-5f35-4406-adea-2c103ac2af5f",
      "title": "Write documentation",
      "description": "Document the API endpoints",
      "status": "TODO",
      "assigneeEmail": null,
      "createdAt": "2025-12-29T22:48:41.113Z",
      "updatedAt": "2025-12-29T22:48:41.113Z",
      "completedAt": null
    }
  ]
}
```

### 5. Complete a Task

Complete a task (must be done by the assignee):

```bash
curl -X POST http://localhost:3000/api/tasks/befde0c6-6955-4732-927b-b6502abe23b3/complete \
  -H "Content-Type: application/json" \
  -d '{
    "completedByEmail": "john@example.com"
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "id": "befde0c6-6955-4732-927b-b6502abe23b3",
    "title": "Implement user authentication",
    "description": "Add JWT-based authentication",
    "status": "COMPLETED",
    "assigneeEmail": "john@example.com",
    "createdAt": "2025-12-29T22:48:32.696Z",
    "updatedAt": "2025-12-29T22:48:49.892Z",
    "completedAt": "2025-12-29T22:48:49.892Z"
  }
}
```

### 6. Business Rule Example: Only Assignee Can Complete

Try to complete a task with a different user:

```bash
curl -X POST http://localhost:3000/api/tasks/befde0c6-6955-4732-927b-b6502abe23b3/complete \
  -H "Content-Type: application/json" \
  -d '{
    "completedByEmail": "jane@example.com"
  }'
```

Response (Error):
```json
{
  "success": false,
  "error": "Only the assigned user can complete this task"
}
```

This demonstrates how business rules are enforced in the domain layer.

### 7. Validation Example: Invalid Email

Try to create a task with an invalid email:

```bash
curl -X POST http://localhost:3000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test task",
    "description": "Testing validation",
    "assigneeEmail": "not-an-email"
  }'
```

Response (Error):
```json
{
  "success": false,
  "error": "Invalid email format"
}
```

### 8. Validation Example: Empty Title

Try to create a task without a title:

```bash
curl -X POST http://localhost:3000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "",
    "description": "Testing validation"
  }'
```

Response (Error):
```json
{
  "success": false,
  "error": "Task title cannot be empty"
}
```

## Testing Multiple Operations

Here's a script that demonstrates a complete workflow:

```bash
#!/bin/bash

# Create a task
echo "Creating task..."
RESPONSE=$(curl -s -X POST http://localhost:3000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Build new feature","description":"Implement the feature","assigneeEmail":"dev@example.com"}')
TASK_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])")
echo "Created task ID: $TASK_ID"

# Get the task
echo "Getting task..."
curl -s http://localhost:3000/api/tasks/$TASK_ID | python3 -m json.tool

# Complete the task
echo "Completing task..."
curl -s -X POST http://localhost:3000/api/tasks/$TASK_ID/complete \
  -H "Content-Type: application/json" \
  -d '{"completedByEmail":"dev@example.com"}' | python3 -m json.tool

# List all tasks
echo "Listing all tasks..."
curl -s http://localhost:3000/api/tasks | python3 -m json.tool
```

## Error Handling

All errors follow a consistent format:

```json
{
  "success": false,
  "error": "Error message here"
}
```

In development mode, stack traces are included for debugging.

## Status Codes

- `200 OK`: Successful GET request
- `201 Created`: Successful POST request (resource created)
- `400 Bad Request`: Validation error or business rule violation
- `404 Not Found`: Resource not found
