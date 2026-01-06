import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Heading,
  Input,
  Stack,
  Text,
} from '@chakra-ui/react';
import { useAuth } from '../contexts/AuthContext';

export function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Redirect if already logged in
  if (isAuthenticated) {
    navigate('/');
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container maxW="container.sm" py={10}>
      <Stack gap={6}>
        <Heading textAlign="center">Login</Heading>

        {error && (
          <Box bg="red.100" p={4} borderRadius="md">
            <Text color="red.700">{error}</Text>
          </Box>
        )}

        <form onSubmit={handleSubmit}>
          <Stack gap={4}>
            <Box>
              <Text mb={2} fontWeight="medium">
                Username
              </Text>
              <Input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                required
              />
            </Box>

            <Box>
              <Text mb={2} fontWeight="medium">
                Password
              </Text>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                required
              />
            </Box>

            <Button
              type="submit"
              variant="outline"
              width="100%"
              loading={isLoading}
            >
              Login
            </Button>
          </Stack>
        </form>

        <Text fontSize="sm" color="gray.500" textAlign="center">
          Default admin credentials: admin / admin
        </Text>
      </Stack>
    </Container>
  );
}
