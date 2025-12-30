import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ChakraProvider, defaultSystem } from '@chakra-ui/react';
import { LandingPage } from './pages/LandingPage';
import { ProductCatalogPage } from './pages/ProductCatalogPage';
import { CartPage } from './pages/CartPage';
import { OrderHistoryPage } from './pages/OrderHistoryPage';

function App() {
  return (
    <ChakraProvider value={defaultSystem}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/products" element={<ProductCatalogPage />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/orders" element={<OrderHistoryPage />} />
        </Routes>
      </BrowserRouter>
    </ChakraProvider>
  );
}

export default App;
