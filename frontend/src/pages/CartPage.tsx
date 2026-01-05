import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Box, Button, Container, Heading, HStack } from '@chakra-ui/react';
import type { Cart, ShippingAddress } from '../types';
import { getCart, updateCartItem, removeFromCart, submitCart } from '../services/api';
import { CartView } from '../components/CartView';
import { ErrorAlert } from '../components/ErrorAlert';

export function CartPage() {
  const [cart, setCart] = useState<Cart | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  const loadCart = async () => {
    try {
      const data = await getCart();
      setCart(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load cart');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCart();
  }, []);

  const handleUpdateQuantity = async (productId: string, quantity: number) => {
    const updatedCart = await updateCartItem(productId, quantity);
    setCart(updatedCart);
  };

  const handleRemoveItem = async (productId: string) => {
    const updatedCart = await removeFromCart(productId);
    setCart(updatedCart);
  };

  const handleSubmit = async (shippingAddress: ShippingAddress) => {
    await submitCart(shippingAddress);
    navigate('/orders');
  };

  return (
    <Container maxW="container.xl" py={6}>
      <HStack justifyContent="space-between" mb={6}>
        <Heading>Shopping Cart</Heading>
        <HStack gap={2}>
          <Link to="/products">
            <Button variant="outline">Continue Shopping</Button>
          </Link>
          <Link to="/">
            <Button variant="ghost">Home</Button>
          </Link>
        </HStack>
      </HStack>

      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

      {isLoading ? (
        <Box textAlign="center" py={10}>Loading cart...</Box>
      ) : cart ? (
        <CartView
          cart={cart}
          onUpdateQuantity={handleUpdateQuantity}
          onRemoveItem={handleRemoveItem}
          onSubmit={handleSubmit}
        />
      ) : null}
    </Container>
  );
}
