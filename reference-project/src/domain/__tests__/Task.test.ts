import { Task } from '../entities/Task';
import { Email } from '../value-objects/Email';
import { TaskStatus } from '../value-objects/TaskStatus';

describe('Task Entity', () => {
  describe('creation', () => {
    it('should create a task with valid data', () => {
      const task = Task.create('Implement feature', 'Add new functionality');

      expect(task.getTitle()).toBe('Implement feature');
      expect(task.getDescription()).toBe('Add new functionality');
      expect(task.getStatus().isTodo()).toBe(true);
      expect(task.getAssigneeEmail()).toBeNull();
    });

    it('should create a task with assignee', () => {
      const email = Email.create('john@example.com');
      const task = Task.create('Implement feature', 'Description', email);

      expect(task.getAssigneeEmail()).not.toBeNull();
      expect(task.getAssigneeEmail()?.getValue()).toBe('john@example.com');
    });

    it('should reject empty title', () => {
      expect(() => {
        Task.create('', 'Description');
      }).toThrow('Task title cannot be empty');
    });

    it('should reject title that is too long', () => {
      const longTitle = 'a'.repeat(201);
      expect(() => {
        Task.create(longTitle, 'Description');
      }).toThrow('Task title cannot exceed 200 characters');
    });
  });

  describe('business rules', () => {
    it('should allow starting progress on a todo task', () => {
      const task = Task.create('Test task', 'Description');

      task.startProgress();

      expect(task.getStatus().isInProgress()).toBe(true);
    });

    it('should prevent starting progress on completed task', () => {
      const task = Task.create('Test task', 'Description');
      const email = Email.create('john@example.com');
      task.assignTo(email);
      task.complete(email);

      expect(() => {
        task.startProgress();
      }).toThrow('Cannot start a completed task');
    });

    it('should allow assignee to complete task', () => {
      const email = Email.create('john@example.com');
      const task = Task.create('Test task', 'Description', email);

      task.complete(email);

      expect(task.getStatus().isCompleted()).toBe(true);
      expect(task.getCompletedAt()).not.toBeNull();
    });

    it('should prevent non-assignee from completing task', () => {
      const assignee = Email.create('john@example.com');
      const other = Email.create('jane@example.com');
      const task = Task.create('Test task', 'Description', assignee);

      expect(() => {
        task.complete(other);
      }).toThrow('Only the assigned user can complete this task');
    });

    it('should prevent modifying completed task', () => {
      const email = Email.create('john@example.com');
      const task = Task.create('Test task', 'Description', email);
      task.complete(email);

      expect(() => {
        task.updateTitle('New title');
      }).toThrow('Cannot modify a completed task');
    });

    it('should allow reopening completed task', () => {
      const email = Email.create('john@example.com');
      const task = Task.create('Test task', 'Description', email);
      task.complete(email);

      task.reopen();

      expect(task.getStatus().isTodo()).toBe(true);
      expect(task.getCompletedAt()).toBeNull();
    });
  });

  describe('assignment', () => {
    it('should assign task to user', () => {
      const task = Task.create('Test task', 'Description');
      const email = Email.create('john@example.com');

      task.assignTo(email);

      expect(task.isAssigned()).toBe(true);
      expect(task.getAssigneeEmail()?.getValue()).toBe('john@example.com');
    });

    it('should update task timestamp when assigned', () => {
      const task = Task.create('Test task', 'Description');
      const initialUpdatedAt = task.getUpdatedAt();

      // Wait a bit to ensure timestamp difference
      const email = Email.create('john@example.com');
      task.assignTo(email);

      expect(task.getUpdatedAt().getTime()).toBeGreaterThanOrEqual(initialUpdatedAt.getTime());
    });
  });
});
