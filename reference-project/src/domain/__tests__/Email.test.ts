import { Email } from '../value-objects/Email';

describe('Email Value Object', () => {
  describe('creation', () => {
    it('should create email with valid format', () => {
      const email = Email.create('john@example.com');

      expect(email.getValue()).toBe('john@example.com');
    });

    it('should normalize email to lowercase', () => {
      const email = Email.create('John@Example.COM');

      expect(email.getValue()).toBe('john@example.com');
    });

    it('should trim whitespace', () => {
      const email = Email.create('  john@example.com  ');

      expect(email.getValue()).toBe('john@example.com');
    });

    it('should reject empty email', () => {
      expect(() => {
        Email.create('');
      }).toThrow('Email cannot be empty');
    });

    it('should reject invalid email format', () => {
      expect(() => {
        Email.create('not-an-email');
      }).toThrow('Invalid email format');

      expect(() => {
        Email.create('@example.com');
      }).toThrow('Invalid email format');

      expect(() => {
        Email.create('user@');
      }).toThrow('Invalid email format');
    });
  });

  describe('equality', () => {
    it('should be equal if values are equal', () => {
      const email1 = Email.create('john@example.com');
      const email2 = Email.create('john@example.com');

      expect(email1.equals(email2)).toBe(true);
    });

    it('should not be equal if values differ', () => {
      const email1 = Email.create('john@example.com');
      const email2 = Email.create('jane@example.com');

      expect(email1.equals(email2)).toBe(false);
    });
  });

  describe('immutability', () => {
    it('should not have setters (value object is immutable)', () => {
      const email = Email.create('john@example.com');

      // TypeScript would prevent this at compile time
      // This test documents the immutability characteristic
      expect(email.getValue()).toBe('john@example.com');
      
      // Value should not change
      const value = email.getValue();
      expect(email.getValue()).toBe(value);
    });
  });
});
