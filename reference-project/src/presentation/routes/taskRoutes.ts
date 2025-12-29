import { Router } from 'express';
import { TaskController } from '../controllers/TaskController';

/**
 * Create task routes
 * 
 * Defines API endpoints for task operations.
 */
export function createTaskRoutes(taskController: TaskController): Router {
  const router = Router();

  // POST /api/tasks - Create a new task
  router.post('/tasks', (req, res, next) => 
    taskController.createTask(req, res, next)
  );

  // GET /api/tasks/:id - Get a task by ID
  router.get('/tasks/:id', (req, res, next) => 
    taskController.getTask(req, res, next)
  );

  // GET /api/tasks - List all tasks
  router.get('/tasks', (req, res, next) => 
    taskController.listTasks(req, res, next)
  );

  // POST /api/tasks/:id/complete - Complete a task
  router.post('/tasks/:id/complete', (req, res, next) => 
    taskController.completeTask(req, res, next)
  );

  return router;
}
