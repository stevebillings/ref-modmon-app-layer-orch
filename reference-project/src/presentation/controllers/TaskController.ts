import { Request, Response, NextFunction } from 'express';
import { CreateTaskUseCase } from '../../application/use-cases/CreateTaskUseCase';
import { GetTaskUseCase } from '../../application/use-cases/GetTaskUseCase';
import { ListTasksUseCase } from '../../application/use-cases/ListTasksUseCase';
import { CompleteTaskUseCase } from '../../application/use-cases/CompleteTaskUseCase';
import { NotFoundError } from '../middleware/errorHandler';

/**
 * Task Controller
 * 
 * Handles HTTP requests related to tasks.
 * Delegates to application layer use cases.
 * Formats HTTP responses.
 * 
 * Responsibilities:
 * - Parse HTTP requests
 * - Call appropriate use case
 * - Format responses
 * - Handle errors
 */
export class TaskController {
  constructor(
    private readonly createTaskUseCase: CreateTaskUseCase,
    private readonly getTaskUseCase: GetTaskUseCase,
    private readonly listTasksUseCase: ListTasksUseCase,
    private readonly completeTaskUseCase: CompleteTaskUseCase
  ) {}

  /**
   * POST /api/tasks
   * Create a new task
   */
  async createTask(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { title, description, assigneeEmail } = req.body;

      const taskDTO = await this.createTaskUseCase.execute({
        title,
        description,
        assigneeEmail,
      });

      res.status(201).json({
        success: true,
        data: taskDTO,
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * GET /api/tasks/:id
   * Get a task by ID
   */
  async getTask(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;

      const taskDTO = await this.getTaskUseCase.execute(id);

      if (!taskDTO) {
        throw new NotFoundError('Task not found');
      }

      res.status(200).json({
        success: true,
        data: taskDTO,
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * GET /api/tasks
   * List all tasks
   */
  async listTasks(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const tasks = await this.listTasksUseCase.execute();

      res.status(200).json({
        success: true,
        data: tasks,
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * POST /api/tasks/:id/complete
   * Mark a task as complete
   */
  async completeTask(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      const { completedByEmail } = req.body;

      const taskDTO = await this.completeTaskUseCase.execute(id, {
        completedByEmail,
      });

      res.status(200).json({
        success: true,
        data: taskDTO,
      });
    } catch (error) {
      next(error);
    }
  }
}
