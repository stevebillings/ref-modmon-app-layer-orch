/**
 * Format a price string for display with dollar sign and two decimal places.
 * @param price - The price as a string (e.g., "19.99" or "5")
 * @returns Formatted price string (e.g., "$19.99" or "$5.00")
 */
export function formatCurrency(price: string): string {
  const numericPrice = parseFloat(price);
  if (isNaN(numericPrice)) {
    return '$0.00';
  }
  return `$${numericPrice.toFixed(2)}`;
}

/**
 * Parse a currency input to a valid price string.
 * Strips non-numeric characters except decimal point.
 * @param input - User input string
 * @returns Cleaned price string suitable for API submission
 */
export function parseCurrencyInput(input: string): string {
  // Remove everything except digits and decimal point
  const cleaned = input.replace(/[^\d.]/g, '');

  // Handle multiple decimal points - keep only the first
  const parts = cleaned.split('.');
  if (parts.length > 2) {
    return parts[0] + '.' + parts.slice(1).join('');
  }

  return cleaned || '0';
}

/**
 * Calculate subtotal for a line item.
 * @param unitPrice - Price per unit as a string
 * @param quantity - Number of units
 * @returns Subtotal as a formatted string
 */
export function calculateSubtotal(unitPrice: string, quantity: number): string {
  const price = parseFloat(unitPrice);
  if (isNaN(price) || quantity < 0) {
    return '0.00';
  }
  return (price * quantity).toFixed(2);
}
