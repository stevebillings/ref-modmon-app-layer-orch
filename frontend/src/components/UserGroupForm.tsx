import { useState } from 'react';
import {
  Box,
  Button,
  Field,
  Heading,
  Input,
  Stack,
  Textarea,
} from '@chakra-ui/react';
import { ErrorAlert } from './ErrorAlert';

interface UserGroupFormProps {
  onSubmit: (name: string, description: string) => Promise<void>;
}

export function UserGroupForm({ onSubmit }: UserGroupFormProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await onSubmit(name.trim(), description.trim());
      setName('');
      setDescription('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create user group');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box borderWidth={1} borderRadius="md" p={4} mb={6}>
      <Heading size="md" mb={4}>
        Create User Group
      </Heading>
      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}
      <form onSubmit={handleSubmit}>
        <Stack gap={4}>
          <Field.Root>
            <Field.Label>Group Name</Field.Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., beta_testers"
              required
            />
            <Field.HelperText>
              Use snake_case for group names (e.g., beta_testers, internal_users)
            </Field.HelperText>
          </Field.Root>
          <Field.Root>
            <Field.Label>Description</Field.Label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the purpose of this group..."
              rows={2}
            />
          </Field.Root>
          <Button type="submit" variant="outline" loading={isLoading}>
            Create Group
          </Button>
        </Stack>
      </form>
    </Box>
  );
}
