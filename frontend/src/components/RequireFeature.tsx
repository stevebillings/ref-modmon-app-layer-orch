import { useAuth } from '../contexts/AuthContext';

interface RequireFeatureProps {
  flag: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * Conditionally renders children based on feature flag status.
 *
 * @example
 * <RequireFeature flag="new_dashboard">
 *   <NewDashboard />
 * </RequireFeature>
 */
export function RequireFeature({
  flag,
  children,
  fallback = null,
}: RequireFeatureProps) {
  const { isFeatureEnabled } = useAuth();

  if (!isFeatureEnabled(flag)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
