import { useState } from 'react';
import {
  Box,
  Button,
  Checkbox,
  CloseButton,
  Dialog,
  HStack,
  Portal,
  Text,
  VStack,
} from '@chakra-ui/react';
import type { ManagedUser, UserGroup } from '../types';
import { ErrorAlert } from './ErrorAlert';

interface UserGroupsManageDialogProps {
  user: ManagedUser | null;
  groups: UserGroup[];
  isOpen: boolean;
  onClose: () => void;
  onAddToGroup: (userId: string, groupId: string) => Promise<void>;
  onRemoveFromGroup: (userId: string, groupId: string) => Promise<void>;
  onRefresh: () => Promise<void>;
}

export function UserGroupsManageDialog({
  user,
  groups,
  isOpen,
  onClose,
  onAddToGroup,
  onRemoveFromGroup,
  onRefresh,
}: UserGroupsManageDialogProps) {
  const [processingGroupId, setProcessingGroupId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleToggleGroup = async (groupId: string, isCurrentlyMember: boolean) => {
    if (!user) return;

    setProcessingGroupId(groupId);
    setError(null);
    try {
      if (isCurrentlyMember) {
        await onRemoveFromGroup(user.id, groupId);
      } else {
        await onAddToGroup(user.id, groupId);
      }
      await onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update group membership');
    } finally {
      setProcessingGroupId(null);
    }
  };

  const handleClose = () => {
    setError(null);
    onClose();
  };

  const isUserInGroup = (groupId: string): boolean => {
    return user?.group_ids.includes(groupId) ?? false;
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(e) => !e.open && handleClose()}>
      <Portal>
        <Dialog.Backdrop />
        <Dialog.Positioner>
          <Dialog.Content>
            <Dialog.Header>
              <Dialog.Title>Manage Groups: {user?.username}</Dialog.Title>
              <Dialog.CloseTrigger asChild>
                <CloseButton size="sm" />
              </Dialog.CloseTrigger>
            </Dialog.Header>
            <Dialog.Body>
              {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

              <VStack gap={3} align="stretch">
                <Text fontSize="sm" color="gray.600">
                  Select which groups this user should belong to.
                  Group membership affects feature flag targeting.
                </Text>

                {groups.length === 0 ? (
                  <Text color="gray.500" fontSize="sm">
                    No groups available. Create groups from the User Groups page first.
                  </Text>
                ) : (
                  <Box>
                    {groups.map((group) => {
                      const isMember = isUserInGroup(group.id);
                      const isProcessing = processingGroupId === group.id;
                      return (
                        <HStack
                          key={group.id}
                          py={2}
                          borderBottomWidth={1}
                          borderColor="gray.100"
                          justify="space-between"
                        >
                          <Checkbox.Root
                            checked={isMember}
                            disabled={isProcessing}
                            onCheckedChange={() => handleToggleGroup(group.id, isMember)}
                          >
                            <Checkbox.HiddenInput />
                            <Checkbox.Control />
                            <Checkbox.Label>
                              <VStack align="start" gap={0}>
                                <Text fontWeight="medium">{group.name}</Text>
                                {group.description && (
                                  <Text fontSize="xs" color="gray.500">
                                    {group.description}
                                  </Text>
                                )}
                              </VStack>
                            </Checkbox.Label>
                          </Checkbox.Root>
                          {isProcessing && (
                            <Text fontSize="xs" color="gray.500">
                              Updating...
                            </Text>
                          )}
                        </HStack>
                      );
                    })}
                  </Box>
                )}
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
