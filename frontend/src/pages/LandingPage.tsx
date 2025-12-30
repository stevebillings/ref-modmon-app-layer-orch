import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Button, Container, Heading, Text, VStack } from '@chakra-ui/react';
import { getCart } from '../services/api';

export function LandingPage() {
  const [cartItemCount, setCartItemCount] = useState(0);

  useEffect(() => {
    getCart()
      .then((cart) => setCartItemCount(cart.item_count))
      .catch(() => setCartItemCount(0));
  }, []);

  return (
    <Container maxW="container.md" py={10}>
      <VStack gap={8}>
        <Heading size="2xl">E-Commerce Store</Heading>
        <Text color="gray.600">
          Welcome to our store. Browse products, add them to your cart, and place orders.
        </Text>

        <VStack gap={4} width="100%">
          <Link to="/products" style={{ width: '100%' }}>
            <Button width="100%" size="lg" colorPalette="blue">
              Product Catalog
            </Button>
          </Link>

          <Link to="/cart" style={{ width: '100%' }}>
            <Button width="100%" size="lg" colorPalette="green">
              Cart {cartItemCount > 0 && `(${cartItemCount} items)`}
            </Button>
          </Link>

          <Link to="/orders" style={{ width: '100%' }}>
            <Button width="100%" size="lg" variant="outline">
              Order History
            </Button>
          </Link>
        </VStack>
      </VStack>
    </Container>
  );
}
