"""Address verification adapter implementations."""

import logging

from application.ports.address_verification import (
    AddressVerificationPort,
    AddressVerificationResult,
    VerificationStatus,
)

logger = logging.getLogger(__name__)


class StubAddressVerificationAdapter(AddressVerificationPort):
    """
    Stub adapter for address verification in testing and development.

    This adapter simulates an external address verification service.
    It always returns verified status except for special test cases:

    - Addresses with "invalid" in street_line_1 return INVALID status
    - Addresses with "undeliverable" in street_line_1 return UNDELIVERABLE status
    - Addresses with "unavailable" in street_line_1 return SERVICE_UNAVAILABLE status
    - All other addresses are standardized (uppercased) and returned as VERIFIED

    This enables testing all code paths without requiring a real external API.
    """

    def verify(
        self,
        street_line_1: str,
        street_line_2: str | None,
        city: str,
        state: str,
        postal_code: str,
        country: str,
    ) -> AddressVerificationResult:
        """
        Verify an address using stub logic.

        Special test cases based on street_line_1 content:
        - Contains "invalid" → INVALID status
        - Contains "undeliverable" → UNDELIVERABLE status
        - Contains "unavailable" → SERVICE_UNAVAILABLE status
        - Otherwise → VERIFIED with standardized (uppercased) address
        """
        street_lower = street_line_1.lower()

        # Test case: simulate invalid address
        if "invalid" in street_lower:
            logger.debug(f"Stub: Marking address as invalid: {street_line_1}")
            return AddressVerificationResult(
                status=VerificationStatus.INVALID,
                standardized_address=None,
                verification_id=None,
                error_message="Address not found or is invalid",
                field_errors={"street_line_1": "Invalid street address"},
            )

        # Test case: simulate undeliverable address
        if "undeliverable" in street_lower:
            logger.debug(f"Stub: Marking address as undeliverable: {street_line_1}")
            return AddressVerificationResult(
                status=VerificationStatus.UNDELIVERABLE,
                standardized_address=None,
                verification_id=None,
                error_message="Address exists but cannot receive deliveries",
                field_errors=None,
            )

        # Test case: simulate service unavailable
        if "unavailable" in street_lower:
            logger.debug("Stub: Simulating service unavailable")
            return AddressVerificationResult(
                status=VerificationStatus.SERVICE_UNAVAILABLE,
                standardized_address=None,
                verification_id=None,
                error_message="Address verification service is temporarily unavailable",
                field_errors=None,
            )

        # Normal case: return verified with standardized (uppercased) address
        standardized = {
            "street_line_1": street_line_1.upper(),
            "street_line_2": street_line_2.upper() if street_line_2 else None,
            "city": city.upper(),
            "state": state.upper(),
            "postal_code": postal_code.upper(),
            "country": country.upper(),
        }

        verification_id = f"STUB-{postal_code}-{hash(street_line_1) % 10000:04d}"

        logger.debug(f"Stub: Address verified successfully: {verification_id}")
        return AddressVerificationResult(
            status=VerificationStatus.VERIFIED,
            standardized_address=standardized,
            verification_id=verification_id,
            error_message=None,
            field_errors=None,
        )


# Singleton instance
_address_verification_adapter: AddressVerificationPort | None = None


def get_address_verification_adapter() -> AddressVerificationPort:
    """
    Get the address verification adapter singleton.

    Returns a StubAddressVerificationAdapter for development/testing.
    In a production environment, this could be extended to return
    a real adapter based on configuration.
    """
    global _address_verification_adapter
    if _address_verification_adapter is None:
        _address_verification_adapter = StubAddressVerificationAdapter()
        logger.info("Initialized stub address verification adapter")
    return _address_verification_adapter
