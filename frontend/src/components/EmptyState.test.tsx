import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ChakraProvider, defaultSystem } from '@chakra-ui/react';
import { EmptyState } from './EmptyState';

function renderWithChakra(ui: React.ReactElement) {
  return render(
    <ChakraProvider value={defaultSystem}>{ui}</ChakraProvider>
  );
}

describe('EmptyState', () => {
  it('displays the message', () => {
    renderWithChakra(<EmptyState message="No items found" />);
    expect(screen.getByText('No items found')).toBeInTheDocument();
  });
});
