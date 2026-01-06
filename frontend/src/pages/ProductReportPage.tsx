import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Heading,
  HStack,
  Input,
  Text,
  VStack,
} from '@chakra-ui/react';
import type { ProductReportItem, ProductReportFilters, ProductReportResponse } from '../types';
import { getProductReport } from '../services/api';
import { ProductReportTable } from '../components/ProductReportTable';
import { ErrorAlert } from '../components/ErrorAlert';

const DEFAULT_PAGE_SIZE = 20;

export function ProductReportPage() {
  const [items, setItems] = useState<ProductReportItem[]>([]);
  const [pagination, setPagination] = useState<Omit<ProductReportResponse, 'results'> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [lowStockThreshold, setLowStockThreshold] = useState('');
  const [hasSales, setHasSales] = useState<boolean | undefined>(undefined);
  const [hasReservations, setHasReservations] = useState<boolean | undefined>(undefined);
  const [showDeleted, setShowDeleted] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  const loadReport = useCallback(async () => {
    setIsLoading(true);
    try {
      const filters: ProductReportFilters = {
        page: currentPage,
        page_size: DEFAULT_PAGE_SIZE,
        search: searchTerm || undefined,
        low_stock_threshold: lowStockThreshold ? parseInt(lowStockThreshold, 10) : undefined,
        has_sales: hasSales,
        has_reservations: hasReservations,
        include_deleted: showDeleted || undefined,
      };

      const data = await getProductReport(filters);
      setItems(data.results);
      setPagination({
        page: data.page,
        page_size: data.page_size,
        total_count: data.total_count,
        total_pages: data.total_pages,
        has_next: data.has_next,
        has_previous: data.has_previous,
      });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load product report');
    } finally {
      setIsLoading(false);
    }
  }, [currentPage, searchTerm, lowStockThreshold, hasSales, hasReservations, showDeleted]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setLowStockThreshold('');
    setHasSales(undefined);
    setHasReservations(undefined);
    setShowDeleted(false);
    setCurrentPage(1);
  };

  const toggleHasSales = () => {
    if (hasSales === undefined) setHasSales(true);
    else if (hasSales === true) setHasSales(false);
    else setHasSales(undefined);
  };

  const toggleHasReservations = () => {
    if (hasReservations === undefined) setHasReservations(true);
    else if (hasReservations === true) setHasReservations(false);
    else setHasReservations(undefined);
  };

  const hasActiveFilters = searchTerm || lowStockThreshold || hasSales !== undefined || hasReservations !== undefined || showDeleted;

  const getFilterButtonLabel = (label: string, value: boolean | undefined) => {
    if (value === undefined) return label;
    if (value === true) return `${label}: Yes`;
    return `${label}: No`;
  };

  const getFilterButtonColor = (value: boolean | undefined) => {
    if (value === undefined) return 'gray';
    if (value === true) return 'green';
    return 'red';
  };

  return (
    <Container maxW="container.xl" py={6}>
      <HStack justifyContent="space-between" mb={6}>
        <Box>
          <Heading size="xl" mb={2}>Product Report</Heading>
          <Text color="gray.600">
            Cross-aggregate view of product inventory, sales, and cart reservations.
          </Text>
        </Box>
        <Link to="/">
          <Button variant="outline">Home</Button>
        </Link>
      </HStack>

      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

      {/* Filter UI */}
      <Box bg="gray.50" p={4} borderRadius="md" mb={6}>
        <VStack gap={4} align="stretch">
          <HStack gap={4} flexWrap="wrap">
            <Input
              placeholder="Search products..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              maxW="250px"
              bg="white"
            />
            <Input
              placeholder="Low stock threshold"
              type="number"
              min="0"
              value={lowStockThreshold}
              onChange={(e) => {
                setLowStockThreshold(e.target.value);
                setCurrentPage(1);
              }}
              maxW="160px"
              bg="white"
            />
            <Button
              variant={hasSales !== undefined ? 'solid' : 'outline'}
              colorPalette={getFilterButtonColor(hasSales)}
              onClick={() => {
                toggleHasSales();
                setCurrentPage(1);
              }}
              size="sm"
            >
              {getFilterButtonLabel('Has Sales', hasSales)}
            </Button>
            <Button
              variant={hasReservations !== undefined ? 'solid' : 'outline'}
              colorPalette={getFilterButtonColor(hasReservations)}
              onClick={() => {
                toggleHasReservations();
                setCurrentPage(1);
              }}
              size="sm"
            >
              {getFilterButtonLabel('In Carts', hasReservations)}
            </Button>
            <Button
              variant={showDeleted ? 'solid' : 'outline'}
              colorPalette={showDeleted ? 'red' : 'gray'}
              onClick={() => {
                setShowDeleted(!showDeleted);
                setCurrentPage(1);
              }}
              size="sm"
            >
              Show Deleted
            </Button>
            {hasActiveFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearFilters}
              >
                Clear Filters
              </Button>
            )}
          </HStack>
        </VStack>
      </Box>

      {isLoading ? (
        <Box textAlign="center" py={10}>
          <Text color="gray.500">Loading report...</Text>
        </Box>
      ) : (
        <ProductReportTable
          items={items}
          pagination={pagination || undefined}
          onPageChange={handlePageChange}
        />
      )}
    </Container>
  );
}
