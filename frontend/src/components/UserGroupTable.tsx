import { useState } from 'react';
import {
  Badge,
  Box,
  Button,
  HStack,
  Table,
  Text,
} from '@chakra-ui/react';
import type { UserGroup } from '../types';
import { ConfirmationDialog } from './ConfirmationDialog';
import { EmptyState } from './EmptyState';
import { ErrorAlert } from './ErrorAlert';

interface UserGroupTableProps {
  groups: UserGroup[];
  onDelete: (id: string) => Promise<void>;
  onManageUsers: (group: UserGroup) => void;
}

export function UserGroupTable({
  groups,
  onDelete,
  onManageUsers,
}: UserGroupTableProps) {
  const [deleteGroup, setDeleteGroup] = useState<UserGroup | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    if (!deleteGroup) return;
    setIsDeleting(true);
    try {
      await onDelete(deleteGroup.id);
      setDeleteGroup(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete group');
      setDeleteGroup(null);
    } finally {
      setIsDeleting(false);
    }
  };

  if (groups.length === 0) {
    return (
      <EmptyState message="No user groups configured. Create your first group to enable feature flag targeting." />
    );
  }

  return (
    <Box>
      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}
      <Table.Root>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>Name</Table.ColumnHeader>
            <Table.ColumnHeader>Description</Table.ColumnHeader>
            <Table.ColumnHeader>Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {groups.map((group) => (
            <Table.Row key={group.id}>
              <Table.Cell>
                <HStack gap={2}>
                  <Text fontFamily="mono" fontSize="sm">
                    {group.name}
                  </Text>
                  <Badge colorPalette="blue" size="sm">
                    Group
                  </Badge>
                </HStack>
              </Table.Cell>
              <Table.Cell>
                <Text fontSize="sm" color="gray.600">
                  {group.description || '—'}
                </Text>
              </Table.Cell>
              <Table.Cell>
                <HStack gap={2}>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onManageUsers(group)}
                  >
                    Manage Users
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setDeleteGroup(group)}
                  >
                    Delete
                  </Button>
                </HStack>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>

      <ConfirmationDialog
        isOpen={deleteGroup !== null}
        onClose={() => setDeleteGroup(null)}
        onConfirm={handleDelete}
        title="Delete User Group"
        message={`Are you sure you want to delete the group "${deleteGroup?.name}"? Users will be removed from this group and any feature flags targeting this group will no longer apply to them.`}
        isLoading={isDeleting}
      />
    </Box>
  );
}
