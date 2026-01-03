import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Heading,
  HStack,
  Input,
  VStack,
} from '@chakra-ui/react';
import type { Product, ProductFilters, ProductListResponse } from '../types';
import { getProducts, createProduct, deleteProduct, restoreProduct, addToCart } from '../services/api';
import { ProductList } from '../components/ProductList';
import { ProductForm } from '../components/ProductForm';
import { ErrorAlert } from '../components/ErrorAlert';
import { useAuth } from '../contexts/AuthContext';

const DEFAULT_PAGE_SIZE = 10;

export function ProductCatalogPage() {
  const { isAdmin } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [pagination, setPagination] = useState<Omit<ProductListResponse, 'results'> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [inStockOnly, setInStockOnly] = useState(false);
  const [showDeleted, setShowDeleted] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  const loadProducts = useCallback(async (filters: ProductFilters = {}) => {
    setIsLoading(true);
    try {
      const data = await getProducts({
        page: filters.page || currentPage,
        page_size: DEFAULT_PAGE_SIZE,
        search: filters.search || searchTerm || undefined,
        min_price: filters.min_price || minPrice || undefined,
        max_price: filters.max_price || maxPrice || undefined,
        in_stock: filters.in_stock !== undefined ? filters.in_stock : (inStockOnly || undefined),
        include_deleted: isAdmin && showDeleted ? true : undefined,
      });
      setProducts(data.results);
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
      setError(err instanceof Error ? err.message : 'Failed to load products');
    } finally {
      setIsLoading(false);
    }
  }, [currentPage, searchTerm, minPrice, maxPrice, inStockOnly, isAdmin, showDeleted]);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  const handleCreateProduct = async (
    name: string,
    price: string,
    stockQuantity: number
  ) => {
    await createProduct(name, price, stockQuantity);
    await loadProducts();
  };

  const handleDeleteProduct = async (productId: string) => {
    await deleteProduct(productId);
    await loadProducts();
  };

  const handleAddToCart = async (productId: string, quantity: number) => {
    await addToCart(productId, quantity);
    await loadProducts();
  };

  const handleRestoreProduct = async (productId: string) => {
    await restoreProduct(productId);
    await loadProducts();
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleSearch = () => {
    setCurrentPage(1); // Reset to first page when searching
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setMinPrice('');
    setMaxPrice('');
    setInStockOnly(false);
    setShowDeleted(false);
    setCurrentPage(1);
  };

  const hasActiveFilters = searchTerm || minPrice || maxPrice || inStockOnly || showDeleted;

  return (
    <Container maxW="container.xl" py={6}>
      <HStack justifyContent="space-between" mb={6}>
        <Heading>Product Catalog</Heading>
        <Link to="/">
          <Button variant="outline">Back to Home</Button>
        </Link>
      </HStack>

      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

      <ProductForm onSubmit={handleCreateProduct} />

      {/* Search and Filter UI */}
      <Box bg="gray.50" p={4} borderRadius="md" mb={6}>
        <VStack gap={4} align="stretch">
          <HStack gap={4} flexWrap="wrap">
            <Input
              placeholder="Search products..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              maxW="300px"
              bg="white"
            />
            <Input
              placeholder="Min price"
              type="number"
              value={minPrice}
              onChange={(e) => setMinPrice(e.target.value)}
              maxW="120px"
              bg="white"
            />
            <Input
              placeholder="Max price"
              type="number"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
              maxW="120px"
              bg="white"
            />
            <Button
              variant={inStockOnly ? 'solid' : 'outline'}
              colorPalette={inStockOnly ? 'green' : 'gray'}
              onClick={() => setInStockOnly(!inStockOnly)}
              size="sm"
            >
              In Stock Only
            </Button>
            {isAdmin && (
              <Button
                variant={showDeleted ? 'solid' : 'outline'}
                colorPalette={showDeleted ? 'red' : 'gray'}
                onClick={() => setShowDeleted(!showDeleted)}
                size="sm"
              >
                Show Deleted
              </Button>
            )}
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
        <Box textAlign="center" py={10}>Loading products...</Box>
      ) : (
        <ProductList
          products={products}
          pagination={pagination || undefined}
          onDelete={handleDeleteProduct}
          onRestore={handleRestoreProduct}
          onAddToCart={handleAddToCart}
          onPageChange={handlePageChange}
        />
      )}
    </Container>
  );
}
