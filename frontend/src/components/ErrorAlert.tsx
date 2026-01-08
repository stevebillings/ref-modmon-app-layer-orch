import { Alert, CloseButton } from '@chakra-ui/react';

interface ErrorAlertProps {
  message: string;
  onClose?: () => void;
}

export function ErrorAlert({ message, onClose }: ErrorAlertProps) {
  return (
    <Alert.Root status="error" mb={4} data-testid="error-alert">
      <Alert.Indicator />
      <Alert.Content>
        <Alert.Title>Error</Alert.Title>
        <Alert.Description>{message}</Alert.Description>
      </Alert.Content>
      {onClose && (
        <CloseButton onClick={onClose} pos="absolute" right={2} top={2} />
      )}
    </Alert.Root>
  );
}
