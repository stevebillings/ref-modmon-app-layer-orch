import { useState } from 'react';
import {
  Box,
  Button,
  Field,
  Heading,
  HStack,
  Input,
  Stack,
  Text,
} from '@chakra-ui/react';
import { ErrorAlert } from './ErrorAlert';
import type { ShippingAddress, VerifiedShippingAddress } from '../types';
import { verifyAddress } from '../services/api';

interface ShippingAddressFormProps {
  onAddressChange: (address: ShippingAddress | null) => void;
  disabled?: boolean;
}

export function ShippingAddressForm({ onAddressChange, disabled }: ShippingAddressFormProps) {
  const [streetLine1, setStreetLine1] = useState('');
  const [streetLine2, setStreetLine2] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [postalCode, setPostalCode] = useState('');
  const [country, setCountry] = useState('US');
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [isVerifying, setIsVerifying] = useState(false);
  const [verifiedAddress, setVerifiedAddress] = useState<VerifiedShippingAddress | null>(null);
  const [showCorrected, setShowCorrected] = useState(false);

  const getCurrentAddress = (): ShippingAddress => ({
    street_line_1: streetLine1,
    street_line_2: streetLine2 || undefined,
    city,
    state,
    postal_code: postalCode,
    country: country || 'US',
  });

  const isFormComplete = streetLine1 && city && state && postalCode;

  const handleVerify = async () => {
    if (!isFormComplete) return;

    setError(null);
    setFieldErrors({});
    setIsVerifying(true);
    setShowCorrected(false);

    try {
      const result = await verifyAddress(getCurrentAddress());

      if (result.verified && result.standardized_address) {
        setVerifiedAddress(result.standardized_address);
        onAddressChange(result.standardized_address);

        if (result.status === 'corrected') {
          setShowCorrected(true);
        }
      } else {
        setVerifiedAddress(null);
        onAddressChange(null);
        setError(result.error_message || 'Address verification failed');
        if (result.field_errors) {
          setFieldErrors(result.field_errors);
        }
      }
    } catch (err) {
      setVerifiedAddress(null);
      onAddressChange(null);
      setError(err instanceof Error ? err.message : 'Failed to verify address');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleInputChange = () => {
    // Clear verification when user edits
    if (verifiedAddress) {
      setVerifiedAddress(null);
      setShowCorrected(false);
      onAddressChange(null);
    }
  };

  const handleUseOriginal = () => {
    // Use the original address as entered
    const address = getCurrentAddress();
    onAddressChange(address);
    setShowCorrected(false);
  };

  return (
    <Box borderWidth={1} borderRadius="md" p={4} mb={4}>
      <Heading size="md" mb={4}>
        Shipping Address
      </Heading>
      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

      <Stack gap={4}>
        <Field.Root invalid={!!fieldErrors.street_line_1}>
          <Field.Label>Street Address</Field.Label>
          <Input
            value={streetLine1}
            onChange={(e) => {
              setStreetLine1(e.target.value);
              handleInputChange();
            }}
            placeholder="123 Main St"
            disabled={disabled}
            required
          />
          {fieldErrors.street_line_1 && (
            <Field.ErrorText>{fieldErrors.street_line_1}</Field.ErrorText>
          )}
        </Field.Root>

        <Field.Root>
          <Field.Label>Street Address Line 2 (Optional)</Field.Label>
          <Input
            value={streetLine2}
            onChange={(e) => {
              setStreetLine2(e.target.value);
              handleInputChange();
            }}
            placeholder="Apt, Suite, Unit, etc."
            disabled={disabled}
          />
        </Field.Root>

        <HStack gap={4}>
          <Field.Root flex={2} invalid={!!fieldErrors.city}>
            <Field.Label>City</Field.Label>
            <Input
              value={city}
              onChange={(e) => {
                setCity(e.target.value);
                handleInputChange();
              }}
              placeholder="City"
              disabled={disabled}
              required
            />
            {fieldErrors.city && (
              <Field.ErrorText>{fieldErrors.city}</Field.ErrorText>
            )}
          </Field.Root>

          <Field.Root flex={1} invalid={!!fieldErrors.state}>
            <Field.Label>State</Field.Label>
            <Input
              value={state}
              onChange={(e) => {
                setState(e.target.value);
                handleInputChange();
              }}
              placeholder="CA"
              maxLength={2}
              disabled={disabled}
              required
            />
            {fieldErrors.state && (
              <Field.ErrorText>{fieldErrors.state}</Field.ErrorText>
            )}
          </Field.Root>

          <Field.Root flex={1} invalid={!!fieldErrors.postal_code}>
            <Field.Label>ZIP Code</Field.Label>
            <Input
              value={postalCode}
              onChange={(e) => {
                setPostalCode(e.target.value);
                handleInputChange();
              }}
              placeholder="12345"
              disabled={disabled}
              required
            />
            {fieldErrors.postal_code && (
              <Field.ErrorText>{fieldErrors.postal_code}</Field.ErrorText>
            )}
          </Field.Root>
        </HStack>

        <Field.Root>
          <Field.Label>Country</Field.Label>
          <Input
            value={country}
            onChange={(e) => {
              setCountry(e.target.value);
              handleInputChange();
            }}
            placeholder="US"
            disabled={disabled}
          />
        </Field.Root>

        <Button
          onClick={handleVerify}
          colorPalette="gray"
          variant="outline"
          loading={isVerifying}
          disabled={!isFormComplete || disabled}
        >
          Verify Address
        </Button>

        {showCorrected && verifiedAddress && (
          <Box bg="blue.50" p={3} borderRadius="md">
            <Text fontWeight="bold" mb={2}>
              Address was standardized:
            </Text>
            <Text>{verifiedAddress.street_line_1}</Text>
            {verifiedAddress.street_line_2 && (
              <Text>{verifiedAddress.street_line_2}</Text>
            )}
            <Text>
              {verifiedAddress.city}, {verifiedAddress.state} {verifiedAddress.postal_code}
            </Text>
            <HStack mt={2} gap={2}>
              <Button size="sm" colorPalette="blue" onClick={() => setShowCorrected(false)}>
                Use Standardized
              </Button>
              <Button size="sm" variant="outline" onClick={handleUseOriginal}>
                Use Original
              </Button>
            </HStack>
          </Box>
        )}

        {verifiedAddress && !showCorrected && (
          <Text color="green.600" fontSize="sm">
            Address verified
          </Text>
        )}
      </Stack>
    </Box>
  );
}
