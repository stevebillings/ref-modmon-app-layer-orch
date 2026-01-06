import { useAuth } from '../contexts/AuthContext';
import type { Capability } from '../constants/capabilities';

interface RequireCapabilityProps {
  capability: Capability;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * Conditionally renders children based on user capability.
 *
 * @example
 * <RequireCapability capability={Capabilities.PRODUCTS_CREATE}>
 *   <CreateProductButton />
 * </RequireCapability>
 */
export function RequireCapability({
  capability,
  children,
  fallback = null,
}: RequireCapabilityProps) {
  const { hasCapability } = useAuth();

  if (!hasCapability(capability)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
