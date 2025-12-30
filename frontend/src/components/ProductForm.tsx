import { useState } from 'react';
import {
  Box,
  Button,
  Field,
  Heading,
  Input,
  Stack,
} from '@chakra-ui/react';
import { ErrorAlert } from './ErrorAlert';

interface ProductFormProps {
  onSubmit: (name: string, price: string, stockQuantity: number) => Promise<void>;
}

export function ProductForm({ onSubmit }: ProductFormProps) {
  const [name, setName] = useState('');
  const [price, setPrice] = useState('');
  const [stockQuantity, setStockQuantity] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await onSubmit(name, price, parseInt(stockQuantity, 10) || 0);
      setName('');
      setPrice('');
      setStockQuantity('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create product');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box borderWidth={1} borderRadius="md" p={4} mb={6}>
      <Heading size="md" mb={4}>
        Add New Product
      </Heading>
      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}
      <form onSubmit={handleSubmit}>
        <Stack gap={4}>
          <Field.Root>
            <Field.Label>Product Name</Field.Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter product name"
              required
            />
          </Field.Root>
          <Field.Root>
            <Field.Label>Price ($)</Field.Label>
            <Input
              type="number"
              step="0.01"
              min="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="0.00"
              required
            />
          </Field.Root>
          <Field.Root>
            <Field.Label>Stock Quantity</Field.Label>
            <Input
              type="number"
              min="0"
              value={stockQuantity}
              onChange={(e) => setStockQuantity(e.target.value)}
              placeholder="0"
              required
            />
          </Field.Root>
          <Button type="submit" colorPalette="blue" loading={isLoading}>
            Add Product
          </Button>
        </Stack>
      </form>
    </Box>
  );
}
