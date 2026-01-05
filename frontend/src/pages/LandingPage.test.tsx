import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ChakraProvider, defaultSystem } from '@chakra-ui/react';
import { AuthProvider } from '../contexts/AuthContext';
import { LandingPage } from './LandingPage';

vi.mock('../services/api', () => ({
  getCart: vi.fn().mockResolvedValue({ item_count: 0 }),
  getSession: vi.fn().mockResolvedValue({ authenticated: false, csrf_token: 'test' }),
}));

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <ChakraProvider value={defaultSystem}>
      <AuthProvider>
        <MemoryRouter>{ui}</MemoryRouter>
      </AuthProvider>
    </ChakraProvider>
  );
}

describe('LandingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays the store title', () => {
    renderWithProviders(<LandingPage />);
    expect(screen.getByText('E-Commerce Store')).toBeInTheDocument();
  });

  it('displays navigation buttons', () => {
    renderWithProviders(<LandingPage />);
    expect(screen.getByText('Product Catalog')).toBeInTheDocument();
    expect(screen.getByText(/Cart/)).toBeInTheDocument();
    expect(screen.getByText('Order History')).toBeInTheDocument();
  });
});
