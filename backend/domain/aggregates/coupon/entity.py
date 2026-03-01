"""
Coupon aggregate root.

Business rules enforced here:
- Expiry date check: raises CouponExpiredError if coupon has expired
- Discount calculation: (order_total * discount_percent / 100), rounded to 2 decimal places

The per-user usage limit (has this user already used this coupon?) CANNOT be checked
here because the Coupon aggregate must not import from the Order aggregate — this is
enforced structurally by import-linter. That check is forced into the application layer
(CartService), which is the only legal cross-aggregate coordination point.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from domain.aggregates.coupon.exceptions import CouponExpiredError

if TYPE_CHECKING:
    from domain.events import DomainEvent


@dataclass
class Coupon:
    """
    Coupon aggregate root.

    Use create() factory for new coupons.
    Use constructor directly for reconstitution from persistence.
    """

    id: UUID
    code: str
    discount_percent: Decimal
    expires_at: datetime
    created_at: datetime
    _domain_events: List["DomainEvent"] = field(
        default_factory=list, repr=False, compare=False
    )

    @classmethod
    def create(
        cls,
        code: str,
        discount_percent: Decimal,
        expires_at: datetime,
        actor_id: str = "anonymous",
    ) -> "Coupon":
        """
        Factory method to create a new Coupon.

        Raises:
            ValueError: If code is empty, discount_percent is out of range, or expires_at is in the past.
        """
        from domain.aggregates.coupon.events import CouponCreated

        if not code or not code.strip():
            raise ValueError("Coupon code cannot be empty")
        if discount_percent <= 0 or discount_percent > 100:
            raise ValueError("discount_percent must be between 0 (exclusive) and 100 (inclusive)")
        if expires_at <= datetime.now(timezone.utc):
            raise ValueError("expires_at must be in the future")

        coupon = cls(
            id=uuid4(),
            code=code.strip().upper(),
            discount_percent=discount_percent,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
        )

        coupon._raise_event(
            CouponCreated(
                coupon_id=coupon.id,
                code=coupon.code,
                discount_percent=coupon.discount_percent,
                actor_id=actor_id,
            )
        )

        return coupon

    def validate_and_calculate_discount(
        self,
        order_total: Decimal,
        actor_id: str,
        order_id: Optional[UUID] = None,
    ) -> Decimal:
        """
        Validate this coupon is still valid and calculate the discount amount.

        Checks expiry only — per-user limit check is STRUCTURALLY FORCED into the
        application layer by import-linter (Coupon cannot import Order).

        Args:
            order_total: The pre-discount order subtotal
            actor_id: ID of the actor applying the coupon (for audit event)
            order_id: The order being created (for CouponApplied event)

        Returns:
            The discount amount (order_total * discount_percent / 100), rounded to 2dp

        Raises:
            CouponExpiredError: If the coupon has expired
        """
        from domain.aggregates.coupon.events import CouponApplied

        if datetime.now(timezone.utc) > self.expires_at:
            raise CouponExpiredError(self.code)

        discount_amount = (
            (order_total * self.discount_percent / Decimal("100"))
            .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )

        self._raise_event(
            CouponApplied(
                coupon_id=self.id,
                code=self.code,
                discount_percent=self.discount_percent,
                discount_amount=discount_amount,
                order_id=order_id or uuid4(),
                actor_id=actor_id,
            )
        )

        return discount_amount

    def _raise_event(self, event: "DomainEvent") -> None:
        """Record a domain event."""
        self._domain_events.append(event)

    def get_domain_events(self) -> List["DomainEvent"]:
        """Return all collected events."""
        return list(self._domain_events)

    def clear_domain_events(self) -> None:
        """Clear collected events after dispatch."""
        self._domain_events = []
