import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Heading,
  HStack,
  Input,
  Stack,
  Table,
  Text,
} from '@chakra-ui/react';
import type { Coupon, CreateCouponRequest } from '../../types';
import { createCoupon, listCoupons } from '../../services/api';
import { ErrorAlert } from '../../components/ErrorAlert';

export function CouponsPage() {
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [code, setCode] = useState('');
  const [discountPercent, setDiscountPercent] = useState('');
  const [expiresAt, setExpiresAt] = useState('');

  useEffect(() => {
    loadCoupons();
  }, []);

  const loadCoupons = async () => {
    try {
      const data = await listCoupons();
      setCoupons(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load coupons');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = async () => {
    setFormError(null);
    if (!code.trim() || !discountPercent || !expiresAt) {
      setFormError('All fields are required');
      return;
    }

    setIsCreating(true);
    try {
      const request: CreateCouponRequest = {
        code: code.trim().toUpperCase(),
        discount_percent: discountPercent,
        expires_at: new Date(expiresAt).toISOString(),
      };
      const newCoupon = await createCoupon(request);
      setCoupons((prev) => [newCoupon, ...prev]);
      setCode('');
      setDiscountPercent('');
      setExpiresAt('');
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create coupon');
    } finally {
      setIsCreating(false);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return dateStr;
    }
  };

  const isExpired = (expiresAt: string) => new Date(expiresAt) < new Date();

  return (
    <Container maxW="container.xl" py={6}>
      <HStack justifyContent="space-between" mb={6}>
        <Heading>Coupons</Heading>
        <Link to="/">
          <Button variant="ghost">Home</Button>
        </Link>
      </HStack>

      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

      <Box mb={8} p={4} borderWidth={1} borderRadius="md">
        <Heading size="md" mb={4}>Create Coupon</Heading>
        {formError && <ErrorAlert message={formError} onClose={() => setFormError(null)} />}
        <Stack gap={3} maxW="400px">
          <Box>
            <Text fontWeight="medium" mb={1}>Code</Text>
            <Input
              placeholder="e.g. SAVE10"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
            />
          </Box>
          <Box>
            <Text fontWeight="medium" mb={1}>Discount (%)</Text>
            <Input
              type="number"
              min="1"
              max="100"
              placeholder="e.g. 10"
              value={discountPercent}
              onChange={(e) => setDiscountPercent(e.target.value)}
            />
          </Box>
          <Box>
            <Text fontWeight="medium" mb={1}>Expires At</Text>
            <Input
              type="datetime-local"
              value={expiresAt}
              onChange={(e) => setExpiresAt(e.target.value)}
            />
          </Box>
          <Button
            onClick={handleCreate}
            loading={isCreating}
            disabled={!code.trim() || !discountPercent || !expiresAt}
          >
            Create Coupon
          </Button>
        </Stack>
      </Box>

      <Heading size="md" mb={4}>All Coupons</Heading>
      {isLoading ? (
        <Text>Loading...</Text>
      ) : coupons.length === 0 ? (
        <Text color="gray.500">No coupons yet.</Text>
      ) : (
        <Table.Root>
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>Code</Table.ColumnHeader>
              <Table.ColumnHeader>Discount</Table.ColumnHeader>
              <Table.ColumnHeader>Expires At</Table.ColumnHeader>
              <Table.ColumnHeader>Status</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {coupons.map((coupon) => (
              <Table.Row key={coupon.id}>
                <Table.Cell fontWeight="medium">{coupon.code}</Table.Cell>
                <Table.Cell>{coupon.discount_percent}%</Table.Cell>
                <Table.Cell>{formatDate(coupon.expires_at)}</Table.Cell>
                <Table.Cell>
                  <Text color={isExpired(coupon.expires_at) ? 'red.500' : 'green.600'}>
                    {isExpired(coupon.expires_at) ? 'Expired' : 'Active'}
                  </Text>
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      )}
    </Container>
  );
}
