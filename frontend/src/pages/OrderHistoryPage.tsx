import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Box, Button, Container, Heading, HStack } from '@chakra-ui/react';
import type { Order } from '../types';
import { getOrders } from '../services/api';
import { OrderList } from '../components/OrderList';
import { ErrorAlert } from '../components/ErrorAlert';

export function OrderHistoryPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getOrders()
      .then((data) => {
        setOrders(data);
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load orders');
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  return (
    <Container maxW="container.xl" py={6}>
      <HStack justifyContent="space-between" mb={6}>
        <Heading>Order History</Heading>
        <HStack gap={2}>
          <Link to="/products">
            <Button variant="outline">Shop More</Button>
          </Link>
          <Link to="/">
            <Button variant="ghost">Home</Button>
          </Link>
        </HStack>
      </HStack>

      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

      {isLoading ? (
        <Box textAlign="center" py={10}>Loading orders...</Box>
      ) : (
        <OrderList orders={orders} />
      )}
    </Container>
  );
}
