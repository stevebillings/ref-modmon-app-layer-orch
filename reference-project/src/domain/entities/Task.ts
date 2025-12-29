import { TaskId } from '../value-objects/TaskId';
import { Email } from '../value-objects/Email';
import { TaskStatus } from '../value-objects/TaskStatus';

/**
 * Task Entity - Aggregate Root
 * 
 * Represents a task in the task management system.
 * Encapsulates business rules and maintains invariants.
 * 
 * Key characteristics:
 * - Has unique identity (TaskId)
 * - Contains rich behavior, not just data
 * - Protects invariants through encapsulation
 * - No public setters - behavior through methods
 */
export class Task {
  private readonly id: TaskId;
  private title!: string;  // Definite assignment assertion - set in constructor via setTitle()
  private description: string;
  private status: TaskStatus;
  private assigneeEmail: Email | null;
  private readonly createdAt: Date;
  private updatedAt: Date;
  private completedAt: Date | null;

  constructor(
    id: TaskId,
    title: string,
    description: string,
    assigneeEmail: Email | null = null
  ) {
    this.id = id;
    this.status = TaskStatus.todo();
    this.createdAt = new Date();
    this.updatedAt = new Date();
    this.completedAt = null;

    // Validate and set title
    this.setTitle(title);
    this.description = description;
    this.assigneeEmail = assigneeEmail;
  }

  /**
   * Static factory method for creating new tasks
   */
  static create(
    title: string,
    description: string,
    assigneeEmail: Email | null = null
  ): Task {
    return new Task(TaskId.create(), title, description, assigneeEmail);
  }

  /**
   * Reconstitute task from persistence
   */
  static reconstitute(
    id: TaskId,
    title: string,
    description: string,
    status: TaskStatus,
    assigneeEmail: Email | null,
    createdAt: Date,
    updatedAt: Date,
    completedAt: Date | null
  ): Task {
    const task = new Task(id, title, description, assigneeEmail);
    task.status = status;
    task.updatedAt = updatedAt;
    task.completedAt = completedAt;
    // Override createdAt via reflection (private field)
    (task as any).createdAt = createdAt;
    return task;
  }

  // Getters
  getId(): TaskId {
    return this.id;
  }

  getTitle(): string {
    return this.title;
  }

  getDescription(): string {
    return this.description;
  }

  getStatus(): TaskStatus {
    return this.status;
  }

  getAssigneeEmail(): Email | null {
    return this.assigneeEmail;
  }

  getCreatedAt(): Date {
    return this.createdAt;
  }

  getUpdatedAt(): Date {
    return this.updatedAt;
  }

  getCompletedAt(): Date | null {
    return this.completedAt;
  }

  // Business methods

  /**
   * Update task title with validation
   */
  updateTitle(newTitle: string): void {
    this.ensureNotCompleted();
    this.setTitle(newTitle);
    this.touch();
  }

  /**
   * Update task description
   */
  updateDescription(newDescription: string): void {
    this.ensureNotCompleted();
    this.description = newDescription;
    this.touch();
  }

  /**
   * Assign task to a user
   */
  assignTo(email: Email): void {
    this.ensureNotCompleted();
    this.assigneeEmail = email;
    this.touch();
  }

  /**
   * Start working on the task
   */
  startProgress(): void {
    if (this.status.isCompleted()) {
      throw new Error('Cannot start a completed task');
    }

    if (this.status.isInProgress()) {
      throw new Error('Task is already in progress');
    }

    this.status = TaskStatus.inProgress();
    this.touch();
  }

  /**
   * Mark task as complete
   * Business rule: Only assigned user can complete the task
   */
  complete(completedByEmail: Email): void {
    if (this.status.isCompleted()) {
      throw new Error('Task is already completed');
    }

    // Business rule: Only assignee can complete the task
    if (this.assigneeEmail && !this.assigneeEmail.equals(completedByEmail)) {
      throw new Error('Only the assigned user can complete this task');
    }

    this.status = TaskStatus.completed();
    this.completedAt = new Date();
    this.touch();
  }

  /**
   * Reopen a completed task
   */
  reopen(): void {
    if (!this.status.isCompleted()) {
      throw new Error('Only completed tasks can be reopened');
    }

    this.status = TaskStatus.todo();
    this.completedAt = null;
    this.touch();
  }

  /**
   * Check if task is assigned
   */
  isAssigned(): boolean {
    return this.assigneeEmail !== null;
  }

  // Private helper methods

  private setTitle(title: string): void {
    const trimmed = title.trim();
    if (!trimmed) {
      throw new Error('Task title cannot be empty');
    }
    if (trimmed.length > 200) {
      throw new Error('Task title cannot exceed 200 characters');
    }
    this.title = trimmed;
  }

  private ensureNotCompleted(): void {
    if (this.status.isCompleted()) {
      throw new Error('Cannot modify a completed task');
    }
  }

  private touch(): void {
    this.updatedAt = new Date();
  }
}
