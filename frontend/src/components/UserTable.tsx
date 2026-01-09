import { useState } from 'react';
import {
  Badge,
  Box,
  Button,
  HStack,
  Table,
  Text,
} from '@chakra-ui/react';
import type { ManagedUser, UserGroup } from '../types';
import { EmptyState } from './EmptyState';
import { ErrorAlert } from './ErrorAlert';

interface UserTableProps {
  users: ManagedUser[];
  groups: UserGroup[];
  onChangeRole: (user: ManagedUser) => void;
  onManageGroups: (user: ManagedUser) => void;
}

export function UserTable({
  users,
  groups,
  onChangeRole,
  onManageGroups,
}: UserTableProps) {
  const [error, setError] = useState<string | null>(null);

  // Helper to get group names from IDs
  const getGroupNames = (groupIds: string[]): string[] => {
    return groupIds
      .map((id) => groups.find((g) => g.id === id)?.name)
      .filter((name): name is string => name !== undefined);
  };

  if (users.length === 0) {
    return (
      <EmptyState message="No users found." />
    );
  }

  return (
    <Box>
      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}
      <Table.Root>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>Username</Table.ColumnHeader>
            <Table.ColumnHeader>Email</Table.ColumnHeader>
            <Table.ColumnHeader>Role</Table.ColumnHeader>
            <Table.ColumnHeader>Groups</Table.ColumnHeader>
            <Table.ColumnHeader>Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {users.map((user) => {
            const groupNames = getGroupNames(user.group_ids);
            return (
              <Table.Row key={user.id}>
                <Table.Cell>
                  <Text fontWeight="medium">{user.username}</Text>
                </Table.Cell>
                <Table.Cell>
                  <Text fontSize="sm" color="gray.600">
                    {user.email || '—'}
                  </Text>
                </Table.Cell>
                <Table.Cell>
                  <Badge
                    colorPalette={user.role === 'admin' ? 'purple' : 'gray'}
                    size="sm"
                  >
                    {user.role}
                  </Badge>
                </Table.Cell>
                <Table.Cell>
                  {groupNames.length === 0 ? (
                    <Text fontSize="sm" color="gray.500">None</Text>
                  ) : (
                    <HStack gap={1} flexWrap="wrap">
                      {groupNames.map((name) => (
                        <Badge key={name} colorPalette="blue" size="sm">
                          {name}
                        </Badge>
                      ))}
                    </HStack>
                  )}
                </Table.Cell>
                <Table.Cell>
                  <HStack gap={2}>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onChangeRole(user)}
                    >
                      Change Role
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onManageGroups(user)}
                    >
                      Manage Groups
                    </Button>
                  </HStack>
                </Table.Cell>
              </Table.Row>
            );
          })}
        </Table.Body>
      </Table.Root>
    </Box>
  );
}
