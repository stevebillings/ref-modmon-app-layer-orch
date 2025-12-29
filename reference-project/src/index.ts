import express, { Application } from 'express';
import { InMemoryTaskRepository } from './infrastructure/persistence/repositories/InMemoryTaskRepository';
import { CreateTaskUseCase } from './application/use-cases/CreateTaskUseCase';
import { GetTaskUseCase } from './application/use-cases/GetTaskUseCase';
import { ListTasksUseCase } from './application/use-cases/ListTasksUseCase';
import { CompleteTaskUseCase } from './application/use-cases/CompleteTaskUseCase';
import { TaskController } from './presentation/controllers/TaskController';
import { createTaskRoutes } from './presentation/routes/taskRoutes';
import { errorHandler } from './presentation/middleware/errorHandler';

/**
 * Application entry point
 * 
 * Sets up dependency injection and starts the server.
 * This is where we wire together all the layers.
 */

// Infrastructure layer - create repository
const taskRepository = new InMemoryTaskRepository();

// Application layer - create use cases
const createTaskUseCase = new CreateTaskUseCase(taskRepository);
const getTaskUseCase = new GetTaskUseCase(taskRepository);
const listTasksUseCase = new ListTasksUseCase(taskRepository);
const completeTaskUseCase = new CompleteTaskUseCase(taskRepository);

// Presentation layer - create controller
const taskController = new TaskController(
  createTaskUseCase,
  getTaskUseCase,
  listTasksUseCase,
  completeTaskUseCase
);

// Express app setup
const app: Application = express();

// Middleware
app.use(express.json());

// Routes
app.use('/api', createTaskRoutes(taskController));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Error handling middleware (must be last)
app.use(errorHandler);

// Start server
const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`API endpoint: http://localhost:${PORT}/api/tasks`);
});

export { app };
