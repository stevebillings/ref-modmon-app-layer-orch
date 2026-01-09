import { useEffect, useState } from 'react';
import {
  Badge,
  Box,
  Button,
  CloseButton,
  Dialog,
  HStack,
  List,
  Portal,
  Text,
  VStack,
} from '@chakra-ui/react';
import type { FeatureFlag, UserGroup } from '../types';
import { ErrorAlert } from './ErrorAlert';

interface FeatureFlagTargetsDialogProps {
  flag: FeatureFlag | null;
  groups: UserGroup[];
  isOpen: boolean;
  onClose: () => void;
  onAddTarget: (flagName: string, groupId: string) => Promise<void>;
  onRemoveTarget: (flagName: string, groupId: string) => Promise<void>;
}

export function FeatureFlagTargetsDialog({
  flag,
  groups,
  isOpen,
  onClose,
  onAddTarget,
  onRemoveTarget,
}: FeatureFlagTargetsDialogProps) {
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentTargets, setCurrentTargets] = useState<string[]>([]);

  useEffect(() => {
    if (flag) {
      setCurrentTargets(flag.target_group_ids);
    }
  }, [flag]);

  const handleAddTarget = async (groupId: string) => {
    if (!flag) return;
    setIsLoading(groupId);
    setError(null);
    try {
      await onAddTarget(flag.name, groupId);
      setCurrentTargets((prev) => [...prev, groupId]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add target');
    } finally {
      setIsLoading(null);
    }
  };

  const handleRemoveTarget = async (groupId: string) => {
    if (!flag) return;
    setIsLoading(groupId);
    setError(null);
    try {
      await onRemoveTarget(flag.name, groupId);
      setCurrentTargets((prev) => prev.filter((id) => id !== groupId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove target');
    } finally {
      setIsLoading(null);
    }
  };

  const handleClose = () => {
    setError(null);
    onClose();
  };

  const targetedGroups = groups.filter((g) => currentTargets.includes(g.id));
  const availableGroups = groups.filter((g) => !currentTargets.includes(g.id));

  return (
    <Dialog.Root open={isOpen} onOpenChange={(e) => !e.open && handleClose()}>
      <Portal>
        <Dialog.Backdrop />
        <Dialog.Positioner>
          <Dialog.Content>
            <Dialog.Header>
              <Dialog.Title>
                Target Groups: {flag?.name}
              </Dialog.Title>
              <Dialog.CloseTrigger asChild>
                <CloseButton size="sm" />
              </Dialog.CloseTrigger>
            </Dialog.Header>
            <Dialog.Body>
              {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

              <VStack gap={4} align="stretch">
                <Box p={3} bg="blue.50" borderRadius="md">
                  <Text fontSize="sm" color="blue.800">
                    {currentTargets.length === 0 ? (
                      <>This flag is <strong>enabled for all users</strong> (no targeting).</>
                    ) : (
                      <>This flag is <strong>only enabled for users in the targeted groups</strong> below.</>
                    )}
                  </Text>
                </Box>

                <Box>
                  <Text fontWeight="medium" mb={2}>
                    Targeted Groups ({targetedGroups.length})
                  </Text>
                  {targetedGroups.length === 0 ? (
                    <Text color="gray.500" fontSize="sm">
                      No groups targeted. Flag applies to all users when enabled.
                    </Text>
                  ) : (
                    <List.Root gap={2}>
                      {targetedGroups.map((group) => (
                        <List.Item key={group.id}>
                          <HStack justify="space-between" width="100%">
                            <HStack gap={2}>
                              <Text fontFamily="mono" fontSize="sm">
                                {group.name}
                              </Text>
                              <Badge colorPalette="green" size="sm">
                                Targeted
                              </Badge>
                            </HStack>
                            <Button
                              size="xs"
                              variant="ghost"
                              colorPalette="red"
                              onClick={() => handleRemoveTarget(group.id)}
                              loading={isLoading === group.id}
                            >
                              Remove
                            </Button>
                          </HStack>
                        </List.Item>
                      ))}
                    </List.Root>
                  )}
                </Box>

                {availableGroups.length > 0 && (
                  <Box>
                    <Text fontWeight="medium" mb={2}>
                      Available Groups ({availableGroups.length})
                    </Text>
                    <List.Root gap={2}>
                      {availableGroups.map((group) => (
                        <List.Item key={group.id}>
                          <HStack justify="space-between" width="100%">
                            <Text fontFamily="mono" fontSize="sm">
                              {group.name}
                            </Text>
                            <Button
                              size="xs"
                              variant="outline"
                              onClick={() => handleAddTarget(group.id)}
                              loading={isLoading === group.id}
                            >
                              Add
                            </Button>
                          </HStack>
                        </List.Item>
                      ))}
                    </List.Root>
                  </Box>
                )}

                {groups.length === 0 && (
                  <Box p={3} bg="gray.50" borderRadius="md">
                    <Text fontSize="sm" color="gray.600">
                      No user groups exist yet. Create groups in the User Groups page to enable targeting.
                    </Text>
                  </Box>
                )}
              </VStack>
            </Dialog.Body>
            <Dialog.Footer>
              <Button variant="outline" onClick={handleClose}>
                Done
              </Button>
            </Dialog.Footer>
          </Dialog.Content>
        </Dialog.Positioner>
      </Portal>
    </Dialog.Root>
  );
}
