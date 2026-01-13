"""Value objects for the Order aggregate."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class UnverifiedAddress:
    """
    Value object representing an address before verification.

    Used as input to the address verification service. This address
    has not yet been validated or standardized.
    """

    street_line_1: str
    street_line_2: Optional[str]
    city: str
    state: str
    postal_code: str
    country: str  # ISO 3166-1 alpha-2 code, e.g., "US"


@dataclass(frozen=True)
class VerifiedAddress:
    """
    Value object representing an address that has been verified.

    Contains the standardized/corrected address from the verification service.
    This address is guaranteed to have been validated by an external service.
    """

    street_line_1: str
    street_line_2: Optional[str]
    city: str
    state: str
    postal_code: str
    country: str
    verification_id: str  # ID from the verification service for audit trail

    @classmethod
    def from_unverified(
        cls,
        original: UnverifiedAddress,
        standardized: Dict[str, Any],
        verification_id: str,
    ) -> "VerifiedAddress":
        """
        Create a VerifiedAddress from verification service response.

        Args:
            original: The original unverified address
            standardized: Dict with standardized address fields from the service
            verification_id: Unique ID from the verification service

        Returns:
            A new VerifiedAddress with standardized values
        """
        return cls(
            street_line_1=standardized.get("street_line_1", original.street_line_1),
            street_line_2=standardized.get("street_line_2", original.street_line_2),
            city=standardized.get("city", original.city),
            state=standardized.get("state", original.state),
            postal_code=standardized.get("postal_code", original.postal_code),
            country=standardized.get("country", original.country),
            verification_id=verification_id,
        )

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert to dictionary for serialization."""
        return {
            "street_line_1": self.street_line_1,
            "street_line_2": self.street_line_2,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
            "verification_id": self.verification_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerifiedAddress":
        """Create from dictionary (for deserialization from database)."""
        return cls(
            street_line_1=data.get("street_line_1", ""),
            street_line_2=data.get("street_line_2"),
            city=data.get("city", ""),
            state=data.get("state", ""),
            postal_code=data.get("postal_code", ""),
            country=data.get("country", ""),
            verification_id=data.get("verification_id", ""),
        )
