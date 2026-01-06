import { useState } from 'react';
import {
  Badge,
  Box,
  Button,
  HStack,
  Switch,
  Table,
  Text,
} from '@chakra-ui/react';
import type { FeatureFlag } from '../types';
import { ConfirmationDialog } from './ConfirmationDialog';
import { EmptyState } from './EmptyState';
import { ErrorAlert } from './ErrorAlert';

interface FeatureFlagTableProps {
  flags: FeatureFlag[];
  onToggle: (name: string, enabled: boolean) => Promise<void>;
  onDelete: (name: string) => Promise<void>;
}

export function FeatureFlagTable({
  flags,
  onToggle,
  onDelete,
}: FeatureFlagTableProps) {
  const [deleteFlag, setDeleteFlag] = useState<FeatureFlag | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [togglingFlag, setTogglingFlag] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleToggle = async (flag: FeatureFlag) => {
    setTogglingFlag(flag.name);
    setError(null);
    try {
      await onToggle(flag.name, !flag.enabled);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle flag');
    } finally {
      setTogglingFlag(null);
    }
  };

  const handleDelete = async () => {
    if (!deleteFlag) return;
    setIsDeleting(true);
    try {
      await onDelete(deleteFlag.name);
      setDeleteFlag(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete flag');
      setDeleteFlag(null);
    } finally {
      setIsDeleting(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (flags.length === 0) {
    return (
      <EmptyState message="No feature flags configured. Create your first flag to get started." />
    );
  }

  return (
    <Box>
      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}
      <Table.Root>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>Name</Table.ColumnHeader>
            <Table.ColumnHeader>Status</Table.ColumnHeader>
            <Table.ColumnHeader>Description</Table.ColumnHeader>
            <Table.ColumnHeader>Last Updated</Table.ColumnHeader>
            <Table.ColumnHeader>Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {flags.map((flag) => (
            <Table.Row key={flag.name}>
              <Table.Cell>
                <Text fontFamily="mono" fontSize="sm">
                  {flag.name}
                </Text>
              </Table.Cell>
              <Table.Cell>
                <HStack gap={3}>
                  <Switch.Root
                    checked={flag.enabled}
                    onCheckedChange={() => handleToggle(flag)}
                    disabled={togglingFlag === flag.name}
                  >
                    <Switch.HiddenInput />
                    <Switch.Control />
                  </Switch.Root>
                  <Badge colorPalette={flag.enabled ? 'green' : 'gray'}>
                    {flag.enabled ? 'Enabled' : 'Disabled'}
                  </Badge>
                </HStack>
              </Table.Cell>
              <Table.Cell>
                <Text fontSize="sm" color="gray.600">
                  {flag.description || '—'}
                </Text>
              </Table.Cell>
              <Table.Cell>
                <Text fontSize="sm" color="gray.500">
                  {formatDate(flag.updated_at)}
                </Text>
              </Table.Cell>
              <Table.Cell>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setDeleteFlag(flag)}
                >
                  Delete
                </Button>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>

      <ConfirmationDialog
        isOpen={deleteFlag !== null}
        onClose={() => setDeleteFlag(null)}
        onConfirm={handleDelete}
        title="Delete Feature Flag"
        message={`Are you sure you want to delete the flag "${deleteFlag?.name}"? Any code checking this flag will start receiving "false" (disabled).`}
        isLoading={isDeleting}
      />
    </Box>
  );
}
