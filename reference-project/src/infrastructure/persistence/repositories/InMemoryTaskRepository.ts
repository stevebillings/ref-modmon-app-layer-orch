import { Task } from '../../../domain/entities/Task';
import { TaskId } from '../../../domain/value-objects/TaskId';
import { Email } from '../../../domain/value-objects/Email';
import { ITaskRepository } from '../../../domain/repositories/ITaskRepository';

/**
 * In-Memory implementation of Task Repository
 * 
 * This is a simple implementation for demonstration purposes.
 * In production, this would be replaced with a database implementation
 * (e.g., PostgreSQL, MongoDB).
 * 
 * Note: This implementation is in the infrastructure layer,
 * while the interface is defined in the domain layer.
 */
export class InMemoryTaskRepository implements ITaskRepository {
  private tasks: Map<string, Task> = new Map();

  async findById(id: TaskId): Promise<Task | null> {
    const task = this.tasks.get(id.getValue());
    return task || null;
  }

  async findByAssignee(email: Email): Promise<Task[]> {
    const tasks: Task[] = [];
    for (const task of this.tasks.values()) {
      const assignee = task.getAssigneeEmail();
      if (assignee && assignee.equals(email)) {
        tasks.push(task);
      }
    }
    return tasks;
  }

  async findAll(): Promise<Task[]> {
    return Array.from(this.tasks.values());
  }

  async save(task: Task): Promise<void> {
    this.tasks.set(task.getId().getValue(), task);
  }

  async delete(id: TaskId): Promise<void> {
    this.tasks.delete(id.getValue());
  }

  async exists(id: TaskId): Promise<boolean> {
    return this.tasks.has(id.getValue());
  }

  // Helper method for testing
  clear(): void {
    this.tasks.clear();
  }

  // Helper method for testing
  count(): number {
    return this.tasks.size;
  }
}
