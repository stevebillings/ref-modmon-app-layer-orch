import {
  Badge,
  Box,
  Button,
  HStack,
  Table,
  Text,
} from '@chakra-ui/react';
import type { ProductReportItem } from '../types';
import { formatCurrency } from '../services/currencyUtils';
import { EmptyState } from './EmptyState';

interface PaginationInfo {
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

interface ProductReportTableProps {
  items: ProductReportItem[];
  pagination?: PaginationInfo;
  onPageChange?: (page: number) => void;
}

export function ProductReportTable({
  items,
  pagination,
  onPageChange,
}: ProductReportTableProps) {
  if (items.length === 0) {
    return (
      <EmptyState message="No products match the current filters." />
    );
  }

  return (
    <Box>
      <Table.Root>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>Product Name</Table.ColumnHeader>
            <Table.ColumnHeader textAlign="right">Price</Table.ColumnHeader>
            <Table.ColumnHeader textAlign="right">Stock</Table.ColumnHeader>
            <Table.ColumnHeader textAlign="right">Reserved</Table.ColumnHeader>
            <Table.ColumnHeader textAlign="right">Total Sold</Table.ColumnHeader>
            <Table.ColumnHeader textAlign="center">Status</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {items.map((item) => (
            <Table.Row
              key={item.product_id}
              opacity={item.is_deleted ? 0.6 : 1}
              bg={item.is_deleted ? 'red.50' : undefined}
            >
              <Table.Cell>
                <HStack gap={2}>
                  <Text textDecoration={item.is_deleted ? 'line-through' : undefined}>
                    {item.name}
                  </Text>
                </HStack>
              </Table.Cell>
              <Table.Cell textAlign="right">{formatCurrency(item.price)}</Table.Cell>
              <Table.Cell textAlign="right">
                <Text
                  color={item.stock_quantity <= 10 ? 'orange.600' : undefined}
                  fontWeight={item.stock_quantity <= 10 ? 'bold' : undefined}
                >
                  {item.stock_quantity}
                </Text>
              </Table.Cell>
              <Table.Cell textAlign="right">
                {item.currently_reserved > 0 ? (
                  <Badge colorPalette="blue">{item.currently_reserved}</Badge>
                ) : (
                  <Text color="gray.400">0</Text>
                )}
              </Table.Cell>
              <Table.Cell textAlign="right">
                {item.total_sold > 0 ? (
                  <Badge colorPalette="green">{item.total_sold}</Badge>
                ) : (
                  <Text color="gray.400">0</Text>
                )}
              </Table.Cell>
              <Table.Cell textAlign="center">
                {item.is_deleted ? (
                  <Badge colorPalette="red">Deleted</Badge>
                ) : item.stock_quantity === 0 ? (
                  <Badge colorPalette="orange">Out of Stock</Badge>
                ) : (
                  <Badge colorPalette="green">Active</Badge>
                )}
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>

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
