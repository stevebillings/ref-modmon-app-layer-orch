import { Box, Heading, Table, Text } from '@chakra-ui/react';
import type { Order } from '../types';
import { formatCurrency, calculateSubtotal } from '../services/currencyUtils';
import { EmptyState } from './EmptyState';

interface OrderListProps {
  orders: Order[];
}

export function OrderList({ orders }: OrderListProps) {
  if (orders.length === 0) {
    return (
      <EmptyState message="No orders yet. Submit your cart to create your first order." />
    );
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <Box>
      {orders.map((order) => (
        <Box
          key={order.id}
          data-testid={`order-item-${order.id}`}
          borderWidth={1}
          borderRadius="md"
          p={4}
          mb={4}
        >
          <Heading size="sm" mb={2}>
            Order placed: {formatDate(order.submitted_at)}
          </Heading>
          <Table.Root size="sm">
            <Table.Header>
              <Table.Row>
                <Table.ColumnHeader>Product</Table.ColumnHeader>
                <Table.ColumnHeader>Unit Price</Table.ColumnHeader>
                <Table.ColumnHeader>Quantity</Table.ColumnHeader>
                <Table.ColumnHeader>Subtotal</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {order.items.map((item) => (
                <Table.Row key={item.id}>
                  <Table.Cell>{item.product_name}</Table.Cell>
                  <Table.Cell>{formatCurrency(item.unit_price)}</Table.Cell>
                  <Table.Cell>{item.quantity}</Table.Cell>
                  <Table.Cell>
                    {formatCurrency(calculateSubtotal(item.unit_price, item.quantity))}
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table.Root>
          <Text fontWeight="bold" textAlign="right" mt={2}>
            Total: {formatCurrency(order.total)}
          </Text>
        </Box>
      ))}
    </Box>
  );
}
