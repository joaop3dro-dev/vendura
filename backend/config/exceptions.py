from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from apps.carts.exceptions import EmptyCartError
from apps.coupons.exceptions import (
    CouponExpiredError,
    CouponMinimumOrderValueError,
    CouponNotActivatedError,
    CouponNotFoundError,
    CouponUsageLimitReachedError,
)
from apps.customers.exceptions import (
    CustomerNotFoundError,
    DeliveryAddressNotFoundError,
)
from apps.orders.exceptions import (
    OrderCannotBeCancelledError,
    OrderNotFoundError,
)
from apps.products.exceptions import InsufficientStockError, InvalidProductError

EXCEPTION_MAP = {
    CouponNotFoundError: status.HTTP_404_NOT_FOUND,
    CouponExpiredError: status.HTTP_400_BAD_REQUEST,
    CouponUsageLimitReachedError: status.HTTP_409_CONFLICT,
    CouponMinimumOrderValueError: status.HTTP_400_BAD_REQUEST,
    CouponNotActivatedError: status.HTTP_400_BAD_REQUEST,
    OrderCannotBeCancelledError: status.HTTP_400_BAD_REQUEST,
    OrderNotFoundError: status.HTTP_404_NOT_FOUND,
    DeliveryAddressNotFoundError: status.HTTP_404_NOT_FOUND,
    EmptyCartError: status.HTTP_400_BAD_REQUEST,
    InvalidProductError: status.HTTP_400_BAD_REQUEST,
    InsufficientStockError: status.HTTP_409_CONFLICT,
    CustomerNotFoundError: status.HTTP_404_NOT_FOUND,
}


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return response

    for exception_class, status_code in EXCEPTION_MAP.items():
        if isinstance(exc, exception_class):
            return Response(
                {"error": str(exc), "code": exception_class.__name__},
                status=status_code,
            )

    return None
