import { Task } from '../../domain/entities/Task';
import { Email } from '../../domain/value-objects/Email';
import { ITaskRepository } from '../../domain/repositories/ITaskRepository';
import { CreateTaskDTO, TaskDTO } from '../dtos/TaskDTO';

/**
 * Use Case: Create a new task
 * 
 * Application service that orchestrates domain objects to fulfill
 * the task creation use case. Thin layer that delegates to domain.
 */
export class CreateTaskUseCase {
  constructor(private readonly taskRepository: ITaskRepository) {}

  async execute(dto: CreateTaskDTO): Promise<TaskDTO> {
    // Validate input
    if (!dto.title) {
      throw new Error('Title is required');
    }

    // Create value objects
    const assigneeEmail = dto.assigneeEmail 
      ? Email.create(dto.assigneeEmail)
      : null;

    // Create domain entity - domain logic handles validation
    const task = Task.create(
      dto.title,
      dto.description || '',
      assigneeEmail
    );

    // Persist
    await this.taskRepository.save(task);

    // Return DTO
    return this.toDTO(task);
  }

  private toDTO(task: Task): TaskDTO {
    return {
      id: task.getId().getValue(),
      title: task.getTitle(),
      description: task.getDescription(),
      status: task.getStatus().getValue(),
      assigneeEmail: task.getAssigneeEmail()?.getValue() || null,
      createdAt: task.getCreatedAt().toISOString(),
      updatedAt: task.getUpdatedAt().toISOString(),
      completedAt: task.getCompletedAt()?.toISOString() || null,
    };
  }
}
