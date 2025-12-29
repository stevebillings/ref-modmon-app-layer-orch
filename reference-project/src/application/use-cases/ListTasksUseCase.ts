import { ITaskRepository } from '../../domain/repositories/ITaskRepository';
import { TaskDTO } from '../dtos/TaskDTO';

/**
 * Use Case: List all tasks
 * 
 * Query use case that retrieves all tasks.
 */
export class ListTasksUseCase {
  constructor(private readonly taskRepository: ITaskRepository) {}

  async execute(): Promise<TaskDTO[]> {
    const tasks = await this.taskRepository.findAll();

    return tasks.map(task => ({
      id: task.getId().getValue(),
      title: task.getTitle(),
      description: task.getDescription(),
      status: task.getStatus().getValue(),
      assigneeEmail: task.getAssigneeEmail()?.getValue() || null,
      createdAt: task.getCreatedAt().toISOString(),
      updatedAt: task.getUpdatedAt().toISOString(),
      completedAt: task.getCompletedAt()?.toISOString() || null,
    }));
  }
}
