import { TaskStatusEnum } from '../../domain/value-objects/TaskStatus';

/**
 * Data Transfer Object for Task
 * Used to transfer data between layers
 */
export interface TaskDTO {
  id: string;
  title: string;
  description: string;
  status: TaskStatusEnum;
  assigneeEmail: string | null;
  createdAt: string;
  updatedAt: string;
  completedAt: string | null;
}

/**
 * DTO for creating a new task
 */
export interface CreateTaskDTO {
  title: string;
  description: string;
  assigneeEmail?: string;
}

/**
 * DTO for updating a task
 */
export interface UpdateTaskDTO {
  title?: string;
  description?: string;
  assigneeEmail?: string;
}

/**
 * DTO for completing a task
 */
export interface CompleteTaskDTO {
  completedByEmail: string;
}
