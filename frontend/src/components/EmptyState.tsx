import { Box, Text } from '@chakra-ui/react';

interface EmptyStateProps {
  message: string;
}

export function EmptyState({ message }: EmptyStateProps) {
  return (
    <Box
      py={10}
      textAlign="center"
      color="gray.500"
      borderWidth={1}
      borderRadius="md"
      borderStyle="dashed"
    >
      <Text>{message}</Text>
    </Box>
  );
}
