"""Port interface for address verification services."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class VerificationStatus(Enum):
    """Status codes returned by address verification."""

    VERIFIED = "verified"  # Address is valid and deliverable
    CORRECTED = "corrected"  # Address was valid but standardized/corrected
    UNDELIVERABLE = "undeliverable"  # Address exists but cannot receive deliveries
    INVALID = "invalid"  # Address does not exist or is malformed
    SERVICE_UNAVAILABLE = "service_unavailable"  # Verification service is down


@dataclass(frozen=True)
class AddressVerificationResult:
    """
    Value object containing the result of address verification.

    This provides a structured way to communicate verification outcomes
    without coupling to specific service implementations.
    """

    status: VerificationStatus
    standardized_address: Optional[Dict[str, Any]]  # Standardized address fields if verified
    verification_id: Optional[str]  # Tracking ID from the service for audit
    error_message: Optional[str]  # Human-readable error message if failed
    field_errors: Optional[Dict[str, str]]  # Field-specific errors (e.g., {"city": "Not found"})

    @property
    def is_success(self) -> bool:
        """Return True if the address was successfully verified."""
        return self.status in (VerificationStatus.VERIFIED, VerificationStatus.CORRECTED)


class AddressVerificationPort(ABC):
    """
    Port for address verification services.

    Implementations may use external APIs (SmartyStreets, USPS, Google, etc.),
    stub implementations for testing, or local validation rules.

    The port abstracts away the specifics of how addresses are verified,
    allowing the application to switch between providers without changing
    business logic.
    """

    @abstractmethod
    def verify(
        self,
        street_line_1: str,
        street_line_2: Optional[str],
        city: str,
        state: str,
        postal_code: str,
        country: str,
    ) -> AddressVerificationResult:
        """
        Verify an address and return the verification result.

        This method should NOT raise exceptions for verification failures
        (invalid addresses, undeliverable, etc.). Instead, it returns a
        result object with the appropriate status.

        Exceptions are reserved for infrastructure failures that prevent
        verification from completing (network errors, authentication failures).

        Args:
            street_line_1: Primary street address line
            street_line_2: Secondary address line (apt, suite, etc.) or None
            city: City name
            state: State/province code (e.g., "CA", "NY")
            postal_code: ZIP or postal code
            country: ISO 3166-1 alpha-2 country code (e.g., "US")

        Returns:
            AddressVerificationResult with verification outcome and details
        """
        pass
