import logging

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
from apps.payment.exceptions import (
    MercadoPagoConfigurationError,
    MercadoPagoInvalidResponseError,
    MercadoPagoRequestError,
    MercadoPagoUnavailableError,
    PaymentCancellationPendingError,
    PaymentError,
    PaymentNotFoundError,
    PaymentOrderNotAvailableError,
)
from apps.products.exceptions import InsufficientStockError, InvalidProductError

logger = logging.getLogger(__name__)

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
    PaymentNotFoundError: status.HTTP_404_NOT_FOUND,
    MercadoPagoRequestError: status.HTTP_502_BAD_GATEWAY,
    MercadoPagoInvalidResponseError: status.HTTP_502_BAD_GATEWAY,
    PaymentCancellationPendingError: status.HTTP_409_CONFLICT,
    MercadoPagoUnavailableError: status.HTTP_503_SERVICE_UNAVAILABLE,
    PaymentOrderNotAvailableError: status.HTTP_409_CONFLICT,
    MercadoPagoConfigurationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    PaymentError: status.HTTP_500_INTERNAL_SERVER_ERROR,
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

    logger.exception("erro inesperado. path: %s", context["request"].path)

    return None
