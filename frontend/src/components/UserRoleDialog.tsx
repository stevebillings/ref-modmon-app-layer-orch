import { useState } from 'react';
import {
  Button,
  CloseButton,
  Dialog,
  HStack,
  Portal,
  Text,
  VStack,
} from '@chakra-ui/react';
import type { ManagedUser } from '../types';
import { ErrorAlert } from './ErrorAlert';

interface UserRoleDialogProps {
  user: ManagedUser | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdateRole: (userId: string, role: 'admin' | 'customer') => Promise<void>;
}

export function UserRoleDialog({
  user,
  isOpen,
  onClose,
  onUpdateRole,
}: UserRoleDialogProps) {
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const newRole = user?.role === 'admin' ? 'customer' : 'admin';

  const handleUpdate = async () => {
    if (!user) return;

    setIsUpdating(true);
    setError(null);
    try {
      await onUpdateRole(user.id, newRole);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update role');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleClose = () => {
    setError(null);
    onClose();
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(e) => !e.open && handleClose()}>
      <Portal>
        <Dialog.Backdrop />
        <Dialog.Positioner>
          <Dialog.Content>
            <Dialog.Header>
              <Dialog.Title>Change User Role</Dialog.Title>
              <Dialog.CloseTrigger asChild>
                <CloseButton size="sm" />
              </Dialog.CloseTrigger>
            </Dialog.Header>
            <Dialog.Body>
              {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

              <VStack gap={4} align="stretch">
                <Text>
                  Change role for <strong>{user?.username}</strong> from{' '}
                  <strong>{user?.role}</strong> to <strong>{newRole}</strong>?
                </Text>
                {newRole === 'admin' && (
                  <Text fontSize="sm" color="orange.600">
                    Warning: Admin users have access to system administration features.
                  </Text>
                )}
                {newRole === 'customer' && user?.role === 'admin' && (
                  <Text fontSize="sm" color="orange.600">
                    Warning: This user will lose admin access.
                  </Text>
                )}
              </VStack>
            </Dialog.Body>
            <Dialog.Footer>
              <HStack gap={2}>
                <Button variant="outline" onClick={handleClose}>
                  Cancel
                </Button>
                <Button
                  colorPalette={newRole === 'admin' ? 'purple' : 'gray'}
                  onClick={handleUpdate}
                  loading={isUpdating}
                >
                  Change to {newRole}
                </Button>
              </HStack>
            </Dialog.Footer>
          </Dialog.Content>
        </Dialog.Positioner>
      </Portal>
    </Dialog.Root>
  );
}
