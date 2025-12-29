import { Task } from '../entities/Task';
import { TaskId } from '../value-objects/TaskId';
import { Email } from '../value-objects/Email';

/**
 * Repository interface for Task aggregate
 * 
 * Defined in the domain layer but implemented in infrastructure layer.
 * Provides collection-like interface for accessing tasks.
 * 
 * Note: Repository works with aggregate roots only.
 */
export interface ITaskRepository {
  /**
   * Find a task by its unique identifier
   */
  findById(id: TaskId): Promise<Task | null>;

  /**
   * Find all tasks assigned to a specific user
   */
  findByAssignee(email: Email): Promise<Task[]>;

  /**
   * Get all tasks
   */
  findAll(): Promise<Task[]>;

  /**
   * Save a task (create or update)
   */
  save(task: Task): Promise<void>;

  /**
   * Delete a task
   */
  delete(id: TaskId): Promise<void>;

  /**
   * Check if task exists
   */
  exists(id: TaskId): Promise<boolean>;
}
