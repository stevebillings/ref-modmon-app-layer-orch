import { describe, it, expect } from 'vitest';
import {
  formatCurrency,
  parseCurrencyInput,
  calculateSubtotal,
} from './currencyUtils';

describe('formatCurrency', () => {
  it('formats a simple price', () => {
    expect(formatCurrency('19.99')).toBe('$19.99');
  });

  it('formats a whole number price', () => {
    expect(formatCurrency('5')).toBe('$5.00');
  });

  it('formats a price with one decimal place', () => {
    expect(formatCurrency('10.5')).toBe('$10.50');
  });

  it('handles zero', () => {
    expect(formatCurrency('0')).toBe('$0.00');
  });

  it('handles invalid input', () => {
    expect(formatCurrency('invalid')).toBe('$0.00');
  });

  it('handles empty string', () => {
    expect(formatCurrency('')).toBe('$0.00');
  });

  it('handles large numbers', () => {
    expect(formatCurrency('1234567.89')).toBe('$1234567.89');
  });
});

describe('parseCurrencyInput', () => {
  it('removes dollar sign', () => {
    expect(parseCurrencyInput('$19.99')).toBe('19.99');
  });

  it('removes commas', () => {
    expect(parseCurrencyInput('1,234.56')).toBe('1234.56');
  });

  it('handles plain numbers', () => {
    expect(parseCurrencyInput('19.99')).toBe('19.99');
  });

  it('handles empty string', () => {
    expect(parseCurrencyInput('')).toBe('0');
  });

  it('removes non-numeric characters', () => {
    expect(parseCurrencyInput('abc123.45xyz')).toBe('123.45');
  });

  it('handles multiple decimal points', () => {
    expect(parseCurrencyInput('12.34.56')).toBe('12.3456');
  });
});

describe('calculateSubtotal', () => {
  it('calculates subtotal correctly', () => {
    expect(calculateSubtotal('10.00', 3)).toBe('30.00');
  });

  it('handles decimal prices', () => {
    expect(calculateSubtotal('9.99', 2)).toBe('19.98');
  });

  it('handles quantity of 1', () => {
    expect(calculateSubtotal('15.50', 1)).toBe('15.50');
  });

  it('handles quantity of 0', () => {
    expect(calculateSubtotal('10.00', 0)).toBe('0.00');
  });

  it('handles invalid price', () => {
    expect(calculateSubtotal('invalid', 5)).toBe('0.00');
  });

  it('handles negative quantity', () => {
    expect(calculateSubtotal('10.00', -1)).toBe('0.00');
  });
});
