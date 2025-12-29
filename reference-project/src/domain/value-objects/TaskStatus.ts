/**
 * Value Object representing task status
 * Type-safe enumeration
 */
export enum TaskStatusEnum {
  TODO = 'TODO',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED'
}

export class TaskStatus {
  private constructor(private readonly value: TaskStatusEnum) {}

  static todo(): TaskStatus {
    return new TaskStatus(TaskStatusEnum.TODO);
  }

  static inProgress(): TaskStatus {
    return new TaskStatus(TaskStatusEnum.IN_PROGRESS);
  }

  static completed(): TaskStatus {
    return new TaskStatus(TaskStatusEnum.COMPLETED);
  }

  static fromString(value: string): TaskStatus {
    const upperValue = value.toUpperCase();
    if (!Object.values(TaskStatusEnum).includes(upperValue as TaskStatusEnum)) {
      throw new Error(`Invalid task status: ${value}`);
    }
    return new TaskStatus(upperValue as TaskStatusEnum);
  }

  getValue(): TaskStatusEnum {
    return this.value;
  }

  isTodo(): boolean {
    return this.value === TaskStatusEnum.TODO;
  }

  isInProgress(): boolean {
    return this.value === TaskStatusEnum.IN_PROGRESS;
  }

  isCompleted(): boolean {
    return this.value === TaskStatusEnum.COMPLETED;
  }

  equals(other: TaskStatus): boolean {
    return this.value === other.value;
  }

  toString(): string {
    return this.value;
  }
}
