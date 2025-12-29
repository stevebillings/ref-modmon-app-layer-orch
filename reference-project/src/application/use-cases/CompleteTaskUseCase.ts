import { TaskId } from '../../domain/value-objects/TaskId';
import { Email } from '../../domain/value-objects/Email';
import { ITaskRepository } from '../../domain/repositories/ITaskRepository';
import { CompleteTaskDTO, TaskDTO } from '../dtos/TaskDTO';

/**
 * Use Case: Complete a task
 * 
 * Application service that orchestrates the task completion process.
 * Delegates business logic to the domain entity.
 */
export class CompleteTaskUseCase {
  constructor(private readonly taskRepository: ITaskRepository) {}

  async execute(taskId: string, dto: CompleteTaskDTO): Promise<TaskDTO> {
    // Validate input
    if (!dto.completedByEmail) {
      throw new Error('Completed by email is required');
    }

    // Find task
    const id = TaskId.fromString(taskId);
    const task = await this.taskRepository.findById(id);

    if (!task) {
      throw new Error('Task not found');
    }

    // Create value object
    const completedByEmail = Email.create(dto.completedByEmail);

    // Delegate to domain entity - business rules are enforced here
    task.complete(completedByEmail);

    // Persist changes
    await this.taskRepository.save(task);

    // Return DTO
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
