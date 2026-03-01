"""
CouponApplicationService — coupon administration.

Handles admin coupon creation and listing.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List

from application.ports.unit_of_work import UnitOfWork
from domain.aggregates.coupon.entity import Coupon
from domain.aggregates.coupon.exceptions import CouponNotFoundError
from domain.exceptions import PermissionDeniedError
from domain.user_context import UserContext


class CouponApplicationService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def create_coupon(
        self,
        code: str,
        discount_percent: Decimal,
        expires_at: datetime,
        user_context: UserContext,
    ) -> Coupon:
        """
        Create a coupon. Admin only.

        Raises:
            PermissionDeniedError: If the user is not an admin
            ValueError: If coupon fields are invalid
        """
        if not user_context.is_admin():
            raise PermissionDeniedError(
                action="create_coupon",
                reason="Admin access required",
            )

        coupon = Coupon.create(
            code=code,
            discount_percent=discount_percent,
            expires_at=expires_at,
            actor_id=user_context.actor_id,
        )

        saved = self.uow.get_coupon_repository().save(coupon)
        self.uow.collect_events_from(coupon)
        return saved

    def list_coupons(self, user_context: UserContext) -> List[Coupon]:
        """
        List all coupons. Admin only.

        Raises:
            PermissionDeniedError: If the user is not an admin
        """
        if not user_context.is_admin():
            raise PermissionDeniedError(
                action="list_coupons",
                reason="Admin access required",
            )
        return self.uow.get_coupon_repository().get_all()
