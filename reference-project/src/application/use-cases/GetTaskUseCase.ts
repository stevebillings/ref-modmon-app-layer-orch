import { TaskId } from '../../domain/value-objects/TaskId';
import { ITaskRepository } from '../../domain/repositories/ITaskRepository';
import { TaskDTO } from '../dtos/TaskDTO';

/**
 * Use Case: Get a task by ID
 * 
 * Simple query use case that retrieves a task and returns as DTO.
 */
export class GetTaskUseCase {
  constructor(private readonly taskRepository: ITaskRepository) {}

  async execute(taskId: string): Promise<TaskDTO | null> {
    const id = TaskId.fromString(taskId);
    const task = await this.taskRepository.findById(id);

    if (!task) {
      return null;
    }

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
