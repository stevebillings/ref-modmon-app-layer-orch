import { useCallback, useEffect, useState } from 'react';
import {
  Box,
  Button,
  CloseButton,
  Dialog,
  Field,
  HStack,
  Input,
  List,
  Portal,
  Text,
  VStack,
} from '@chakra-ui/react';
import type { UserGroup } from '../types';
import { ErrorAlert } from './ErrorAlert';

interface UserGroupMembersDialogProps {
  group: UserGroup | null;
  isOpen: boolean;
  onClose: () => void;
  onGetUsers: (groupId: string) => Promise<string[]>;
  onAddUser: (groupId: string, userId: string) => Promise<void>;
  onRemoveUser: (groupId: string, userId: string) => Promise<void>;
}

export function UserGroupMembersDialog({
  group,
  isOpen,
  onClose,
  onGetUsers,
  onAddUser,
  onRemoveUser,
}: UserGroupMembersDialogProps) {
  const [userIds, setUserIds] = useState<string[]>([]);
  const [newUserId, setNewUserId] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [removingUserId, setRemovingUserId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadUsers = useCallback(async () => {
    if (!group) return;
    setIsLoading(true);
    setError(null);
    try {
      const users = await onGetUsers(group.id);
      setUserIds(users);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setIsLoading(false);
    }
  }, [group, onGetUsers]);

  useEffect(() => {
    if (isOpen && group) {
      loadUsers();
    }
  }, [isOpen, group, loadUsers]);

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!group || !newUserId.trim()) return;

    setIsAdding(true);
    setError(null);
    try {
      await onAddUser(group.id, newUserId.trim());
      setNewUserId('');
      await loadUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add user');
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemoveUser = async (userId: string) => {
    if (!group) return;

    setRemovingUserId(userId);
    setError(null);
    try {
      await onRemoveUser(group.id, userId);
      await loadUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove user');
    } finally {
      setRemovingUserId(null);
    }
  };

  const handleClose = () => {
    setNewUserId('');
    setError(null);
    setUserIds([]);
    onClose();
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(e) => !e.open && handleClose()}>
      <Portal>
        <Dialog.Backdrop />
        <Dialog.Positioner>
          <Dialog.Content>
            <Dialog.Header>
              <Dialog.Title>
                Manage Users: {group?.name}
              </Dialog.Title>
              <Dialog.CloseTrigger asChild>
                <CloseButton size="sm" />
              </Dialog.CloseTrigger>
            </Dialog.Header>
            <Dialog.Body>
              {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

              <VStack gap={4} align="stretch">
                <Box>
                  <Text fontWeight="medium" mb={2}>Add User</Text>
                  <form onSubmit={handleAddUser}>
                    <HStack>
                      <Field.Root flex={1}>
                        <Input
                          value={newUserId}
                          onChange={(e) => setNewUserId(e.target.value)}
                          placeholder="Enter user ID (UUID)"
                          size="sm"
                        />
                      </Field.Root>
                      <Button
                        type="submit"
                        size="sm"
                        variant="outline"
                        loading={isAdding}
                        disabled={!newUserId.trim()}
                      >
                        Add
                      </Button>
                    </HStack>
                  </form>
                </Box>

                <Box>
                  <Text fontWeight="medium" mb={2}>
                    Current Members ({userIds.length})
                  </Text>
                  {isLoading ? (
                    <Text color="gray.500" fontSize="sm">Loading...</Text>
                  ) : userIds.length === 0 ? (
                    <Text color="gray.500" fontSize="sm">No users in this group</Text>
                  ) : (
                    <List.Root gap={2}>
                      {userIds.map((userId) => (
                        <List.Item key={userId}>
                          <HStack justify="space-between" width="100%">
                            <Text fontFamily="mono" fontSize="sm" truncate>
                              {userId}
                            </Text>
                            <Button
                              size="xs"
                              variant="ghost"
                              colorPalette="red"
                              onClick={() => handleRemoveUser(userId)}
                              loading={removingUserId === userId}
                            >
                              Remove
                            </Button>
                          </HStack>
                        </List.Item>
                      ))}
                    </List.Root>
                  )}
                </Box>
              </VStack>
            </Dialog.Body>
            <Dialog.Footer>
              <Button variant="outline" onClick={handleClose}>
                Close
              </Button>
            </Dialog.Footer>
          </Dialog.Content>
        </Dialog.Positioner>
      </Portal>
    </Dialog.Root>
  );
}
