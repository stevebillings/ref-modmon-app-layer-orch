import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  HStack,
  Input,
  Text,
} from '@chakra-ui/react';
import type { CouponValidationResult } from '../types';
import { validateCoupon } from '../services/api';

interface CouponInputProps {
  cartTotal: string;
  onCouponApplied: (code: string, result: CouponValidationResult) => void;
  onCouponCleared: () => void;
  disabled?: boolean;
}

export function CouponInput({
  cartTotal,
  onCouponApplied,
  onCouponCleared,
  disabled = false,
}: CouponInputProps) {
  const [code, setCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [appliedResult, setAppliedResult] = useState<CouponValidationResult | null>(null);
  const [appliedCode, setAppliedCode] = useState<string | null>(null);

  const handleApply = async () => {
    if (!code.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await validateCoupon(code.trim(), cartTotal);
      setAppliedResult(result);
      setAppliedCode(code.trim().toUpperCase());
      onCouponApplied(code.trim().toUpperCase(), result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid coupon code');
      setAppliedResult(null);
      setAppliedCode(null);
      onCouponCleared();
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    setCode('');
    setAppliedResult(null);
    setAppliedCode(null);
    setError(null);
    onCouponCleared();
  };

  if (appliedResult && appliedCode) {
    return (
      <Box mb={4}>
        <Alert.Root status="success">
          <Alert.Indicator />
          <Alert.Content>
            <Alert.Title>Coupon Applied: {appliedCode}</Alert.Title>
            <Alert.Description>
              {appliedResult.discount_percent}% off — saving ${appliedResult.discount_amount}
            </Alert.Description>
          </Alert.Content>
          <Button size="sm" variant="ghost" onClick={handleClear} ml={2}>
            Remove
          </Button>
        </Alert.Root>
      </Box>
    );
  }

  return (
    <Box mb={4}>
      <Text fontWeight="medium" mb={2}>Coupon Code</Text>
      <HStack>
        <Input
          placeholder="Enter coupon code"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleApply()}
          disabled={disabled || isLoading}
          maxW="300px"
        />
        <Button
          onClick={handleApply}
          loading={isLoading}
          disabled={disabled || !code.trim()}
          variant="outline"
        >
          Apply
        </Button>
      </HStack>
      {error && (
        <Text color="red.500" fontSize="sm" mt={1}>{error}</Text>
      )}
    </Box>
  );
}
