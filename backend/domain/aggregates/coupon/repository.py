from abc import ABC, abstractmethod
from typing import List, Optional

from domain.aggregates.coupon.entity import Coupon


class CouponRepository(ABC):
    @abstractmethod
    def get_by_code(self, code: str) -> Optional[Coupon]:
        """Get a coupon by its code. Returns None if not found."""
        pass

    @abstractmethod
    def get_all(self) -> List[Coupon]:
        """Get all coupons."""
        pass

    @abstractmethod
    def save(self, coupon: Coupon) -> Coupon:
        """Save a coupon (insert or update)."""
        pass
