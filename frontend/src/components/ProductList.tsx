import { useState } from 'react';
import {
  Box,
  Button,
  HStack,
  Input,
  Table,
  Text,
} from '@chakra-ui/react';
import type { Product } from '../types';
import { formatCurrency } from '../services/currencyUtils';
import { ConfirmationDialog } from './ConfirmationDialog';
import { EmptyState } from './EmptyState';
import { ErrorAlert } from './ErrorAlert';

interface PaginationInfo {
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

interface ProductListProps {
  products: Product[];
  pagination?: PaginationInfo;
  onDelete: (productId: string) => Promise<void>;
  onAddToCart: (productId: string, quantity: number) => Promise<void>;
  onPageChange?: (page: number) => void;
}

export function ProductList({
  products,
  pagination,
  onDelete,
  onAddToCart,
  onPageChange,
}: ProductListProps) {
  const [deleteProduct, setDeleteProduct] = useState<Product | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [quantities, setQuantities] = useState<Record<string, number>>({});
  const [addingToCart, setAddingToCart] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    if (!deleteProduct) return;
    setIsDeleting(true);
    try {
      await onDelete(deleteProduct.id);
      setDeleteProduct(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete product');
      setDeleteProduct(null);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleAddToCart = async (product: Product) => {
    const quantity = quantities[product.id] || 1;
    setAddingToCart(product.id);
    setError(null);
    try {
      await onAddToCart(product.id, quantity);
      setQuantities((prev) => ({ ...prev, [product.id]: 1 }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add to cart');
    } finally {
      setAddingToCart(null);
    }
  };

  if (products.length === 0) {
    return (
      <EmptyState message="No products available. Add products to the catalog to get started." />
    );
  }

  return (
    <Box>
      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}
      <Table.Root>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>Name</Table.ColumnHeader>
            <Table.ColumnHeader>Price</Table.ColumnHeader>
            <Table.ColumnHeader>Available Stock</Table.ColumnHeader>
            <Table.ColumnHeader>Quantity</Table.ColumnHeader>
            <Table.ColumnHeader>Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {products.map((product) => (
            <Table.Row key={product.id}>
              <Table.Cell>{product.name}</Table.Cell>
              <Table.Cell>{formatCurrency(product.price)}</Table.Cell>
              <Table.Cell>{product.stock_quantity}</Table.Cell>
              <Table.Cell>
                <Input
                  type="number"
                  min="1"
                  max={product.stock_quantity}
                  value={quantities[product.id] || 1}
                  onChange={(e) =>
                    setQuantities((prev) => ({
                      ...prev,
                      [product.id]: parseInt(e.target.value, 10) || 1,
                    }))
                  }
                  width="80px"
                  disabled={product.stock_quantity === 0}
                />
              </Table.Cell>
              <Table.Cell>
                <HStack gap={2}>
                  <Button
                    size="sm"
                    colorPalette="green"
                    onClick={() => handleAddToCart(product)}
                    loading={addingToCart === product.id}
                    disabled={product.stock_quantity === 0}
                  >
                    Add to Cart
                  </Button>
                  <Button
                    size="sm"
                    colorPalette="red"
                    variant="outline"
                    onClick={() => setDeleteProduct(product)}
                  >
                    Delete
                  </Button>
                </HStack>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>

      <ConfirmationDialog
        isOpen={deleteProduct !== null}
        onClose={() => setDeleteProduct(null)}
        onConfirm={handleDelete}
        title="Delete Product"
        message={`Are you sure you want to delete "${deleteProduct?.name}"? This action cannot be undone.`}
        isLoading={isDeleting}
      />

      {pagination && pagination.total_pages > 1 && (
        <HStack justifyContent="center" mt={6} gap={4}>
          <Button
            size="sm"
            variant="outline"
            onClick={() => onPageChange?.(pagination.page - 1)}
            disabled={!pagination.has_previous}
          >
            Previous
          </Button>
          <Text fontSize="sm">
            Page {pagination.page} of {pagination.total_pages}
            {' '}({pagination.total_count} items)
          </Text>
          <Button
            size="sm"
            variant="outline"
            onClick={() => onPageChange?.(pagination.page + 1)}
            disabled={!pagination.has_next}
          >
            Next
          </Button>
        </HStack>
      )}
    </Box>
  );
}
