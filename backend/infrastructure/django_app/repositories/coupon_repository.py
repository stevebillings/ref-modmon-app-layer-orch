from typing import List, Optional

from domain.aggregates.coupon.entity import Coupon
from domain.aggregates.coupon.repository import CouponRepository
from infrastructure.django_app.models import CouponModel


class DjangoCouponRepository(CouponRepository):
    def get_by_code(self, code: str) -> Optional[Coupon]:
        """Get a coupon by its code. Returns None if not found."""
        try:
            model = CouponModel.objects.get(code=code.upper())
            return self._to_domain(model)
        except CouponModel.DoesNotExist:
            return None

    def get_all(self) -> List[Coupon]:
        """Get all coupons."""
        return [self._to_domain(m) for m in CouponModel.objects.all()]

    def save(self, coupon: Coupon) -> Coupon:
        """Save a coupon (insert or update)."""
        model, _ = CouponModel.objects.update_or_create(
            id=coupon.id,
            defaults={
                "code": coupon.code,
                "discount_percent": coupon.discount_percent,
                "expires_at": coupon.expires_at,
            },
        )
        return self._to_domain(model)

    @staticmethod
    def _to_domain(model: CouponModel) -> Coupon:
        """Convert ORM model to domain entity."""
        return Coupon(
            id=model.id,
            code=model.code,
            discount_percent=model.discount_percent,
            expires_at=model.expires_at,
            created_at=model.created_at,
        )
