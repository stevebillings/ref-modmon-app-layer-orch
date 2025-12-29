import { CreateTaskUseCase } from '../use-cases/CreateTaskUseCase';
import { InMemoryTaskRepository } from '../../infrastructure/persistence/repositories/InMemoryTaskRepository';

describe('CreateTaskUseCase', () => {
  let repository: InMemoryTaskRepository;
  let useCase: CreateTaskUseCase;

  beforeEach(() => {
    repository = new InMemoryTaskRepository();
    useCase = new CreateTaskUseCase(repository);
  });

  it('should create a task successfully', async () => {
    const dto = {
      title: 'Implement feature',
      description: 'Add new functionality',
      assigneeEmail: 'john@example.com',
    };

    const result = await useCase.execute(dto);

    expect(result.title).toBe('Implement feature');
    expect(result.description).toBe('Add new functionality');
    expect(result.assigneeEmail).toBe('john@example.com');
    expect(result.status).toBe('TODO');
    expect(result.id).toBeDefined();
  });

  it('should create task without assignee', async () => {
    const dto = {
      title: 'Implement feature',
      description: 'Add new functionality',
    };

    const result = await useCase.execute(dto);

    expect(result.assigneeEmail).toBeNull();
  });

  it('should persist task in repository', async () => {
    const dto = {
      title: 'Implement feature',
      description: 'Add new functionality',
    };

    const result = await useCase.execute(dto);

    const count = repository.count();
    expect(count).toBe(1);
  });

  it('should reject task without title', async () => {
    const dto = {
      title: '',
      description: 'Add new functionality',
    };

    await expect(useCase.execute(dto)).rejects.toThrow();
  });

  it('should reject task with invalid email', async () => {
    const dto = {
      title: 'Implement feature',
      description: 'Add new functionality',
      assigneeEmail: 'invalid-email',
    };

    await expect(useCase.execute(dto)).rejects.toThrow('Invalid email format');
  });
});
