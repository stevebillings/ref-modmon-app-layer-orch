import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Heading,
  HStack,
  Text,
  VStack,
} from '@chakra-ui/react';
import { useAuth } from '../contexts/AuthContext';
import { getCart } from '../services/api';

export function LandingPage() {
  const [cartItemCount, setCartItemCount] = useState(0);
  const { user, isAuthenticated, isAdmin, logout, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      getCart()
        .then((cart) => setCartItemCount(cart.item_count))
        .catch(() => setCartItemCount(0));
    }
  }, [isAuthenticated]);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <Container maxW="container.md" py={10}>
      <VStack gap={8}>
        <Box width="100%" textAlign="right">
          {loading ? (
            <Text>Loading...</Text>
          ) : isAuthenticated ? (
            <HStack justify="flex-end" gap={4}>
              <Text>
                Logged in as <strong>{user?.username}</strong>
                {isAdmin && ' (Admin)'}
              </Text>
              <Button size="sm" variant="outline" onClick={handleLogout}>
                Logout
              </Button>
            </HStack>
          ) : (
            <Link to="/login">
              <Button size="sm" variant="outline">
                Login
              </Button>
            </Link>
          )}
        </Box>

        <Heading size="2xl">E-Commerce Store</Heading>
        <Text color="gray.600">
          Welcome to our store. Browse products, add them to your cart, and
          place orders.
        </Text>

        <VStack gap={4} width="100%">
          <Link to="/products" style={{ width: '100%' }}>
            <Button width="100%" size="lg" variant="outline">
              Product Catalog
            </Button>
          </Link>

          <Link to="/cart" style={{ width: '100%' }}>
            <Button width="100%" size="lg" variant="outline">
              Cart {cartItemCount > 0 && `(${cartItemCount} items)`}
            </Button>
          </Link>

          <Link to="/orders" style={{ width: '100%' }}>
            <Button width="100%" size="lg" variant="outline">
              Order History
            </Button>
          </Link>

          {isAdmin && (
            <>
              <Link to="/admin/report" style={{ width: '100%' }}>
                <Button width="100%" size="lg" variant="outline">
                  Product Report (Admin)
                </Button>
              </Link>
              <Link to="/admin/flags" style={{ width: '100%' }}>
                <Button width="100%" size="lg" variant="outline">
                  Feature Flags (Admin)
                </Button>
              </Link>
            </>
          )}
        </VStack>

        {!isAuthenticated && (
          <Text fontSize="sm" color="gray.500">
            Login to access your cart and order history
          </Text>
        )}
      </VStack>
    </Container>
  );
}
