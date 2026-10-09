class PaymentError(Exception):
    """Base class for payment-related exceptions."""


class PaymentOrderNotAvailableError(PaymentError):
    """Raised when a payment is attempted for an order that is not available for payment."""


class MercadoPagoError(PaymentError):
    """Raised when there is an error with the Mercado Pago payment provider."""


class MercadoPagoConfigurationError(MercadoPagoError):
    """Raised when there is a configuration error with the Mercado Pago payment provider."""


class MercadoPagoUnavailableError(MercadoPagoError):
    """Raised when the Mercado Pago payment provider is unavailable."""


class MercadoPagoRequestError(MercadoPagoError):
    """Raised when there is an error with a request to the Mercado Pago payment provider."""


class MercadoPagoInvalidResponseError(MercadoPagoError):
    """Raised when the Mercado Pago payment provider returns an invalid response."""


class PaymentCancellationPendingError(PaymentError):
    pass


class PaymentNotFoundError(PaymentError):
    pass
