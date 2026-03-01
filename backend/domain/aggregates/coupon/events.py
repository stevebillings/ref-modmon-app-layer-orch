"""
Domain events for the Coupon aggregate.

Note: All fields have defaults for Python 3.9 dataclass inheritance compatibility.
When constructing events, always provide all field values as keyword arguments.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from domain.events import DomainEvent, _now_utc


@dataclass(frozen=True)
class CouponCreated(DomainEvent):
    """Raised when an admin creates a coupon."""

    coupon_id: UUID = field(default_factory=uuid4)
    code: str = ""
    discount_percent: Decimal = Decimal("0")
    actor_id: str = ""
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=_now_utc)


@dataclass(frozen=True)
class CouponApplied(DomainEvent):
    """Raised when a coupon is applied to an order at cart submission."""

    coupon_id: UUID = field(default_factory=uuid4)
    code: str = ""
    discount_percent: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    order_id: UUID = field(default_factory=uuid4)
    actor_id: str = ""
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=_now_utc)
