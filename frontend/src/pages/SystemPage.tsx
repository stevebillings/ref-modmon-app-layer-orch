import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, Box, Button, Container, Heading, HStack, Text } from '@chakra-ui/react';
import type { FeatureFlag, UserGroup } from '../types';
import {
  addFeatureFlagTarget,
  createFeatureFlag,
  deleteFeatureFlag,
  getFeatureFlags,
  getUserGroups,
  removeFeatureFlagTarget,
  triggerTestError,
  updateFeatureFlag,
} from '../services/api';
import { FeatureFlagForm } from '../components/FeatureFlagForm';
import { FeatureFlagTable } from '../components/FeatureFlagTable';
import { FeatureFlagTargetsDialog } from '../components/FeatureFlagTargetsDialog';
import { ErrorAlert } from '../components/ErrorAlert';

export function SystemPage() {
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [groups, setGroups] = useState<UserGroup[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isTriggering, setIsTriggering] = useState(false);
  const [testErrorTriggered, setTestErrorTriggered] = useState(false);
  const [selectedFlag, setSelectedFlag] = useState<FeatureFlag | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [flagsData, groupsData] = await Promise.all([
        getFeatureFlags(),
        getUserGroups(),
      ]);
      setFlags(flagsData);
      setGroups(groupsData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreate = async (name: string, enabled: boolean, description: string) => {
    await createFeatureFlag({ name, enabled, description });
    await loadData();
  };

  const handleToggle = async (name: string, enabled: boolean) => {
    await updateFeatureFlag(name, { enabled });
    await loadData();
  };

  const handleDelete = async (name: string) => {
    await deleteFeatureFlag(name);
    await loadData();
  };

  const handleManageTargets = (flag: FeatureFlag) => {
    setSelectedFlag(flag);
  };

  const handleAddTarget = async (flagName: string, groupId: string) => {
    await addFeatureFlagTarget(flagName, groupId);
    await loadData();
  };

  const handleRemoveTarget = async (flagName: string, groupId: string) => {
    await removeFeatureFlagTarget(flagName, groupId);
    await loadData();
  };

  const handleCloseTargetsDialog = () => {
    setSelectedFlag(null);
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

  // Keep selectedFlag in sync with updated flags data
  const currentSelectedFlag = selectedFlag
    ? flags.find((f) => f.name === selectedFlag.name) || selectedFlag
    : null;

  return (
    <Container maxW="container.xl" py={6}>
      <HStack justifyContent="space-between" mb={6}>
        <Box>
          <Heading size="xl" mb={2}>
            System
          </Heading>
          <Text color="gray.600">
            System administration and configuration tools.
          </Text>
        </Box>
        <HStack gap={2}>
          <Link to="/admin/user-groups">
            <Button variant="outline">User Groups</Button>
          </Link>
          <Link to="/">
            <Button variant="outline">Home</Button>
          </Link>
        </HStack>
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
          onManageTargets={handleManageTargets}
        />
      )}

      <FeatureFlagTargetsDialog
        flag={currentSelectedFlag}
        groups={groups}
        isOpen={selectedFlag !== null}
        onClose={handleCloseTargetsDialog}
        onAddTarget={handleAddTarget}
        onRemoveTarget={handleRemoveTarget}
      />

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
