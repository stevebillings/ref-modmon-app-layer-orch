from domain.exceptions import DomainError


class CouponNotFoundError(DomainError):
    def __init__(self, code: str):
        super().__init__(f"Coupon '{code}' not found")
        self.code = code


class CouponExpiredError(DomainError):
    def __init__(self, code: str):
        super().__init__(f"Coupon '{code}' has expired")
        self.code = code


class CouponAlreadyUsedError(DomainError):
    def __init__(self, code: str):
        super().__init__(f"Coupon '{code}' has already been used by this account")
        self.code = code
