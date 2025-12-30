import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Box, Button, Container, Heading, HStack } from '@chakra-ui/react';
import type { Product } from '../types';
import { getProducts, createProduct, deleteProduct, addToCart } from '../services/api';
import { ProductList } from '../components/ProductList';
import { ProductForm } from '../components/ProductForm';
import { ErrorAlert } from '../components/ErrorAlert';

export function ProductCatalogPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadProducts = async () => {
    try {
      const data = await getProducts();
      setProducts(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load products');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

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

      {isLoading ? (
        <Box textAlign="center" py={10}>Loading products...</Box>
      ) : (
        <ProductList
          products={products}
          onDelete={handleDeleteProduct}
          onAddToCart={handleAddToCart}
        />
      )}
    </Container>
  );
}
