import { useState } from 'react';
import {
  Box,
  Button,
  Checkbox,
  Field,
  Heading,
  Input,
  Stack,
  Textarea,
} from '@chakra-ui/react';
import { ErrorAlert } from './ErrorAlert';

interface FeatureFlagFormProps {
  onSubmit: (name: string, enabled: boolean, description: string) => Promise<void>;
}

export function FeatureFlagForm({ onSubmit }: FeatureFlagFormProps) {
  const [name, setName] = useState('');
  const [enabled, setEnabled] = useState(false);
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await onSubmit(name.trim(), enabled, description.trim());
      setName('');
      setEnabled(false);
      setDescription('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create feature flag');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box borderWidth={1} borderRadius="md" p={4} mb={6}>
      <Heading size="md" mb={4}>
        Create Feature Flag
      </Heading>
      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}
      <form onSubmit={handleSubmit}>
        <Stack gap={4}>
          <Field.Root>
            <Field.Label>Flag Name</Field.Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., new_checkout_flow"
              required
            />
            <Field.HelperText>
              Use snake_case for flag names (e.g., incident_email_notifications)
            </Field.HelperText>
          </Field.Root>
          <Field.Root>
            <Field.Label>Description</Field.Label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what this flag controls..."
              rows={2}
            />
          </Field.Root>
          <Checkbox.Root
            checked={enabled}
            onCheckedChange={(e) => setEnabled(!!e.checked)}
          >
            <Checkbox.HiddenInput />
            <Checkbox.Control />
            <Checkbox.Label>Enable flag immediately</Checkbox.Label>
          </Checkbox.Root>
          <Button type="submit" colorPalette="blue" loading={isLoading}>
            Create Flag
          </Button>
        </Stack>
      </form>
    </Box>
  );
}
