import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Box, Button, Container, Heading, HStack, Text } from '@chakra-ui/react';
import type { ManagedUser, UserGroup } from '../types';
import {
  addUserToGroupViaUser,
  getUsers,
  getUserGroups,
  removeUserFromGroupViaUser,
  updateUserRole,
} from '../services/api';
import { UserTable } from '../components/UserTable';
import { UserRoleDialog } from '../components/UserRoleDialog';
import { UserGroupsManageDialog } from '../components/UserGroupsManageDialog';
import { ErrorAlert } from '../components/ErrorAlert';

export function UserManagementPage() {
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [groups, setGroups] = useState<UserGroup[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedUserForRole, setSelectedUserForRole] = useState<ManagedUser | null>(null);
  const [selectedUserForGroups, setSelectedUserForGroups] = useState<ManagedUser | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [usersData, groupsData] = await Promise.all([
        getUsers(),
        getUserGroups(),
      ]);
      setUsers(usersData);
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

  const handleChangeRole = (user: ManagedUser) => {
    setSelectedUserForRole(user);
  };

  const handleManageGroups = (user: ManagedUser) => {
    setSelectedUserForGroups(user);
  };

  const handleUpdateRole = async (userId: string, role: 'admin' | 'customer') => {
    await updateUserRole(userId, { role });
    await loadData();
  };

  const handleAddToGroup = async (userId: string, groupId: string) => {
    await addUserToGroupViaUser(userId, groupId);
  };

  const handleRemoveFromGroup = async (userId: string, groupId: string) => {
    await removeUserFromGroupViaUser(userId, groupId);
  };

  // Keep selected user in sync with updated data
  const currentSelectedUserForGroups = selectedUserForGroups
    ? users.find((u) => u.id === selectedUserForGroups.id) || selectedUserForGroups
    : null;

  return (
    <Container maxW="container.xl" py={6}>
      <HStack justifyContent="space-between" mb={6}>
        <Box>
          <Heading size="xl" mb={2}>
            User Management
          </Heading>
          <Text color="gray.600">
            Manage user roles and group memberships.
          </Text>
        </Box>
        <HStack gap={2}>
          <Link to="/admin/user-groups">
            <Button variant="outline">User Groups</Button>
          </Link>
          <Link to="/admin/system">
            <Button variant="outline">System</Button>
          </Link>
          <Link to="/">
            <Button variant="outline">Home</Button>
          </Link>
        </HStack>
      </HStack>

      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

      {isLoading ? (
        <Box textAlign="center" py={10}>
          <Text color="gray.500">Loading users...</Text>
        </Box>
      ) : (
        <UserTable
          users={users}
          groups={groups}
          onChangeRole={handleChangeRole}
          onManageGroups={handleManageGroups}
        />
      )}

      <UserRoleDialog
        user={selectedUserForRole}
        isOpen={selectedUserForRole !== null}
        onClose={() => setSelectedUserForRole(null)}
        onUpdateRole={handleUpdateRole}
      />

      <UserGroupsManageDialog
        user={currentSelectedUserForGroups}
        groups={groups}
        isOpen={selectedUserForGroups !== null}
        onClose={() => setSelectedUserForGroups(null)}
        onAddToGroup={handleAddToGroup}
        onRemoveFromGroup={handleRemoveFromGroup}
        onRefresh={loadData}
      />
    </Container>
  );
}
