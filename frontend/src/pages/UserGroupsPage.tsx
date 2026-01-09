import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Box, Button, Container, Heading, HStack, Text } from '@chakra-ui/react';
import type { UserGroup } from '../types';
import {
  addUserToGroup,
  createUserGroup,
  deleteUserGroup,
  getUserGroups,
  getUsersInGroup,
  removeUserFromGroup,
} from '../services/api';
import { UserGroupForm } from '../components/UserGroupForm';
import { UserGroupTable } from '../components/UserGroupTable';
import { UserGroupMembersDialog } from '../components/UserGroupMembersDialog';
import { ErrorAlert } from '../components/ErrorAlert';

export function UserGroupsPage() {
  const [groups, setGroups] = useState<UserGroup[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedGroup, setSelectedGroup] = useState<UserGroup | null>(null);

  const loadGroups = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await getUserGroups();
      setGroups(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load user groups');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGroups();
  }, [loadGroups]);

  const handleCreate = async (name: string, description: string) => {
    await createUserGroup({ name, description });
    await loadGroups();
  };

  const handleDelete = async (id: string) => {
    await deleteUserGroup(id);
    await loadGroups();
  };

  const handleManageUsers = (group: UserGroup) => {
    setSelectedGroup(group);
  };

  const handleGetUsers = async (groupId: string) => {
    return getUsersInGroup(groupId);
  };

  const handleAddUser = async (groupId: string, userId: string) => {
    await addUserToGroup(groupId, userId);
  };

  const handleRemoveUser = async (groupId: string, userId: string) => {
    await removeUserFromGroup(groupId, userId);
  };

  return (
    <Container maxW="container.xl" py={6}>
      <HStack justifyContent="space-between" mb={6}>
        <Box>
          <Heading size="xl" mb={2}>
            User Groups
          </Heading>
          <Text color="gray.600">
            Manage user groups for feature flag targeting. Groups allow you to enable
            features for specific sets of users.
          </Text>
        </Box>
        <HStack gap={2}>
          <Link to="/admin/system">
            <Button variant="outline">System</Button>
          </Link>
          <Link to="/">
            <Button variant="outline">Home</Button>
          </Link>
        </HStack>
      </HStack>

      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

      <UserGroupForm onSubmit={handleCreate} />

      {isLoading ? (
        <Box textAlign="center" py={10}>
          <Text color="gray.500">Loading user groups...</Text>
        </Box>
      ) : (
        <UserGroupTable
          groups={groups}
          onDelete={handleDelete}
          onManageUsers={handleManageUsers}
        />
      )}

      <UserGroupMembersDialog
        group={selectedGroup}
        isOpen={selectedGroup !== null}
        onClose={() => setSelectedGroup(null)}
        onGetUsers={handleGetUsers}
        onAddUser={handleAddUser}
        onRemoveUser={handleRemoveUser}
      />
    </Container>
  );
}
