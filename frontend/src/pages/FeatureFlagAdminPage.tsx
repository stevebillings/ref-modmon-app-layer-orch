import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Box, Button, Container, Heading, HStack, Text } from '@chakra-ui/react';
import type { FeatureFlag } from '../types';
import {
  createFeatureFlag,
  deleteFeatureFlag,
  getFeatureFlags,
  triggerTestError,
  updateFeatureFlag,
} from '../services/api';
import { FeatureFlagForm } from '../components/FeatureFlagForm';
import { FeatureFlagTable } from '../components/FeatureFlagTable';
import { ErrorAlert } from '../components/ErrorAlert';

export function FeatureFlagAdminPage() {
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isTriggering, setIsTriggering] = useState(false);
  const [testErrorTriggered, setTestErrorTriggered] = useState(false);

  const loadFlags = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await getFeatureFlags();
      setFlags(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load feature flags');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFlags();
  }, [loadFlags]);

  const handleCreate = async (name: string, enabled: boolean, description: string) => {
    await createFeatureFlag({ name, enabled, description });
    await loadFlags();
  };

  const handleToggle = async (name: string, enabled: boolean) => {
    await updateFeatureFlag(name, { enabled });
    await loadFlags();
  };

  const handleDelete = async (name: string) => {
    await deleteFeatureFlag(name);
    await loadFlags();
  };

  const handleTriggerTestError = async () => {
    setIsTriggering(true);
    setTestErrorTriggered(false);
    try {
      await triggerTestError();
    } catch {
      // Expected - the endpoint returns 500
    }
    setTestErrorTriggered(true);
    setIsTriggering(false);
  };

  return (
    <Container maxW="container.xl" py={6}>
      <HStack justifyContent="space-between" mb={6}>
        <Box>
          <Heading size="xl" mb={2}>
            Feature Flags
          </Heading>
          <Text color="gray.600">
            Manage feature flags to control feature availability without code deployments.
          </Text>
        </Box>
        <Link to="/">
          <Button variant="outline">Home</Button>
        </Link>
      </HStack>

      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

      <FeatureFlagForm onSubmit={handleCreate} />

      {isLoading ? (
        <Box textAlign="center" py={10}>
          <Text color="gray.500">Loading feature flags...</Text>
        </Box>
      ) : (
        <FeatureFlagTable
          flags={flags}
          onToggle={handleToggle}
          onDelete={handleDelete}
        />
      )}

      {/* Test Error Section */}
      <Box mt={10} p={4} borderWidth={1} borderRadius="md" bg="gray.50">
        <Heading size="md" mb={2}>
          Test Incident Notification
        </Heading>
        <Text color="gray.600" mb={4}>
          Trigger a test 500 error to verify incident email notifications are working.
          Make sure the <code>incident_email_notifications</code> flag is enabled first.
        </Text>
        <HStack gap={4}>
          <Button
            variant="outline"
            onClick={handleTriggerTestError}
            loading={isTriggering}
          >
            Trigger Test Error
          </Button>
          {testErrorTriggered && (
            <Alert.Root status="success" variant="subtle" width="auto">
              <Alert.Indicator />
              <Alert.Title>Error triggered! Check the server console for the email.</Alert.Title>
            </Alert.Root>
          )}
        </HStack>
      </Box>
    </Container>
  );
}
