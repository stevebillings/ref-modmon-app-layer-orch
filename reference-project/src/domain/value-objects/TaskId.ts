import { v4 as uuidv4 } from 'uuid';

/**
 * Value Object representing a unique Task identifier
 * Immutable and self-validating
 */
export class TaskId {
  private constructor(private readonly value: string) {
    if (!value || value.trim().length === 0) {
      throw new Error('TaskId cannot be empty');
    }
  }

  /**
   * Create a new random TaskId
   */
  static create(): TaskId {
    return new TaskId(uuidv4());
  }

  /**
   * Create TaskId from existing string value
   */
  static fromString(value: string): TaskId {
    return new TaskId(value);
  }

  /**
   * Get the string value
   */
  getValue(): string {
    return this.value;
  }

  /**
   * Value objects are equal if all their attributes are equal
   */
  equals(other: TaskId): boolean {
    return this.value === other.value;
  }

  toString(): string {
    return this.value;
  }
}
