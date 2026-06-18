class CouponError(Exception):
    pass


class CouponNotFoundError(CouponError):
    pass


class CouponExpiredError(CouponError):
    pass


class CouponUsageLimitReachedError(CouponError):
    pass


class CouponNotActivatedError(CouponError):
    pass


class CouponMinimumOrderValueError(CouponError):
    pass
