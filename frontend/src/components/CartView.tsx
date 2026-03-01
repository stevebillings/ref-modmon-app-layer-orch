import { useState } from 'react';
import {
  Box,
  Button,
  Flex,
  Heading,
  HStack,
  Table,
  Text,
} from '@chakra-ui/react';
import type { Cart, CouponValidationResult, ShippingAddress } from '../types';
import { formatCurrency, calculateSubtotal } from '../services/currencyUtils';
import { ConfirmationDialog } from './ConfirmationDialog';
import { CouponInput } from './CouponInput';
import { EmptyState } from './EmptyState';
import { ErrorAlert } from './ErrorAlert';
import { ShippingAddressForm } from './ShippingAddressForm';

interface CartViewProps {
  cart: Cart;
  onUpdateQuantity: (productId: string, quantity: number) => Promise<void>;
  onRemoveItem: (productId: string) => Promise<void>;
  onSubmit: (shippingAddress: ShippingAddress, couponCode?: string) => Promise<void>;
}

export function CartView({
  cart,
  onUpdateQuantity,
  onRemoveItem,
  onSubmit,
}: CartViewProps) {
  const [removeItemId, setRemoveItemId] = useState<string | null>(null);
  const [isRemoving, setIsRemoving] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [updatingItemId, setUpdatingItemId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [shippingAddress, setShippingAddress] = useState<ShippingAddress | null>(null);
  const [appliedCouponCode, setAppliedCouponCode] = useState<string | undefined>(undefined);
  const [couponResult, setCouponResult] = useState<CouponValidationResult | null>(null);

  const handleRemove = async () => {
    if (!removeItemId) return;
    setIsRemoving(true);
    try {
      await onRemoveItem(removeItemId);
      setRemoveItemId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove item');
      setRemoveItemId(null);
    } finally {
      setIsRemoving(false);
    }
  };

  const handleQuantityChange = async (productId: string, quantity: number) => {
    if (quantity < 1) return;
    setUpdatingItemId(productId);
    setError(null);
    try {
      await onUpdateQuantity(productId, quantity);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update quantity');
    } finally {
      setUpdatingItemId(null);
    }
  };

  const handleSubmit = async () => {
    if (!shippingAddress) {
      setError('Please enter and verify your shipping address');
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      await onSubmit(shippingAddress, appliedCouponCode);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit order');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCouponApplied = (code: string, result: CouponValidationResult) => {
    setAppliedCouponCode(code);
    setCouponResult(result);
  };

  const handleCouponCleared = () => {
    setAppliedCouponCode(undefined);
    setCouponResult(null);
  };

  const removeItem = cart.items.find((item) => item.product_id === removeItemId);

  if (cart.items.length === 0) {
    return (
      <EmptyState message="Your cart is empty. Browse the product catalog to add items." />
    );
  }

  return (
    <Box>
      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}
      <Table.Root>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>Product</Table.ColumnHeader>
            <Table.ColumnHeader>Unit Price</Table.ColumnHeader>
            <Table.ColumnHeader>Quantity</Table.ColumnHeader>
            <Table.ColumnHeader>Subtotal</Table.ColumnHeader>
            <Table.ColumnHeader>Actions</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {cart.items.map((item) => (
            <Table.Row key={item.id} data-testid={`cart-item-${item.id}`}>
              <Table.Cell>{item.product_name}</Table.Cell>
              <Table.Cell>{formatCurrency(item.unit_price)}</Table.Cell>
              <Table.Cell>
                <HStack gap={2}>
                  <Button
                    size="xs"
                    variant="outline"
                    onClick={() =>
                      handleQuantityChange(item.product_id, item.quantity - 1)
                    }
                    disabled={item.quantity <= 1 || updatingItemId === item.product_id}
                  >
                    -
                  </Button>
                  <Text width="40px" textAlign="center">
                    {item.quantity}
                  </Text>
                  <Button
                    size="xs"
                    variant="outline"
                    onClick={() =>
                      handleQuantityChange(item.product_id, item.quantity + 1)
                    }
                    disabled={updatingItemId === item.product_id}
                  >
                    +
                  </Button>
                </HStack>
              </Table.Cell>
              <Table.Cell>
                {formatCurrency(calculateSubtotal(item.unit_price, item.quantity))}
              </Table.Cell>
              <Table.Cell>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setRemoveItemId(item.product_id)}
                >
                  Remove
                </Button>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>

      <Box mt={6} pt={4} borderTopWidth={1}>
        {couponResult ? (
          <>
            <Text mb={1}>Subtotal: {formatCurrency(cart.total)}</Text>
            <Text mb={1} color="green.600">
              Coupon Discount ({couponResult.discount_percent}% off): −{formatCurrency(couponResult.discount_amount)}
            </Text>
            <Heading size="md" mb={4}>
              Total:{' '}
              {formatCurrency(
                String(
                  parseFloat(cart.total) - parseFloat(couponResult.discount_amount)
                )
              )}
            </Heading>
          </>
        ) : (
          <Heading size="md" mb={4}>Total: {formatCurrency(cart.total)}</Heading>
        )}

        <CouponInput
          cartTotal={cart.total}
          onCouponApplied={handleCouponApplied}
          onCouponCleared={handleCouponCleared}
          disabled={isSubmitting}
        />

        <ShippingAddressForm
          onAddressChange={setShippingAddress}
          disabled={isSubmitting}
        />

        <Flex justifyContent="flex-end">
          <Button
            variant="outline"
            size="lg"
            onClick={handleSubmit}
            loading={isSubmitting}
            disabled={!shippingAddress}
          >
            Submit Order
          </Button>
        </Flex>
      </Box>

      <ConfirmationDialog
        isOpen={removeItemId !== null}
        onClose={() => setRemoveItemId(null)}
        onConfirm={handleRemove}
        title="Remove Item"
        message={`Are you sure you want to remove "${removeItem?.product_name}" from your cart?`}
        confirmText="Remove"
        isLoading={isRemoving}
      />
    </Box>
  );
}
