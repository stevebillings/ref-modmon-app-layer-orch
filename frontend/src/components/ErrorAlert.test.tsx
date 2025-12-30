import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ChakraProvider, defaultSystem } from '@chakra-ui/react';
import { ErrorAlert } from './ErrorAlert';

function renderWithChakra(ui: React.ReactElement) {
  return render(
    <ChakraProvider value={defaultSystem}>{ui}</ChakraProvider>
  );
}

describe('ErrorAlert', () => {
  it('displays the error message', () => {
    renderWithChakra(<ErrorAlert message="Something went wrong" />);
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('displays Error title', () => {
    renderWithChakra(<ErrorAlert message="Test error" />);
    expect(screen.getByText('Error')).toBeInTheDocument();
  });
});
