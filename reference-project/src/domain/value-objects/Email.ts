/**
 * Value Object representing an email address
 * Immutable and self-validating
 */
export class Email {
  private constructor(private readonly value: string) {}

  /**
   * Create an Email with validation
   */
  static create(email: string): Email {
    const trimmed = email.trim().toLowerCase();
    
    if (!trimmed) {
      throw new Error('Email cannot be empty');
    }

    if (!this.isValid(trimmed)) {
      throw new Error('Invalid email format');
    }

    return new Email(trimmed);
  }

  /**
   * Validate email format
   */
  private static isValid(email: string): boolean {
    // Simple regex for demonstration - in production, use a robust library
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
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
  equals(other: Email): boolean {
    return this.value === other.value;
  }

  toString(): string {
    return this.value;
  }
}
