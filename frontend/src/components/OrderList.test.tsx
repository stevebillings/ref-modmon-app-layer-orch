import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ChakraProvider, defaultSystem } from '@chakra-ui/react';
import { OrderList } from './OrderList';
import type { Order } from '../types';

function renderWithChakra(ui: React.ReactElement) {
  return render(
    <ChakraProvider value={defaultSystem}>{ui}</ChakraProvider>
  );
}

describe('OrderList', () => {
  it('displays empty state when no orders', () => {
    renderWithChakra(<OrderList orders={[]} />);
    expect(
      screen.getByText('No orders yet. Submit your cart to create your first order.')
    ).toBeInTheDocument();
  });

  it('displays orders with items', () => {
    const orders: Order[] = [
      {
        id: '1',
        submitted_at: '2024-01-15T10:00:00Z',
        total: '30.00',
        items: [
          {
            id: 'item1',
            order_id: '1',
            product_id: 'prod1',
            product_name: 'Test Product',
            unit_price: '10.00',
            quantity: 3,
          },
        ],
      },
    ];

    renderWithChakra(<OrderList orders={orders} />);
    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('$10.00')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('$30.00')).toBeInTheDocument();
  });

  it('displays multiple orders', () => {
    const orders: Order[] = [
      {
        id: '1',
        submitted_at: '2024-01-15T10:00:00Z',
        total: '20.00',
        items: [
          {
            id: 'item1',
            order_id: '1',
            product_id: 'prod1',
            product_name: 'Product A',
            unit_price: '20.00',
            quantity: 1,
          },
        ],
      },
      {
        id: '2',
        submitted_at: '2024-01-14T10:00:00Z',
        total: '15.00',
        items: [
          {
            id: 'item2',
            order_id: '2',
            product_id: 'prod2',
            product_name: 'Product B',
            unit_price: '15.00',
            quantity: 1,
          },
        ],
      },
    ];

    renderWithChakra(<OrderList orders={orders} />);
    expect(screen.getByText('Product A')).toBeInTheDocument();
    expect(screen.getByText('Product B')).toBeInTheDocument();
  });
});
