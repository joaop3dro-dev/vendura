from .exceptions import PaymentNotFoundError
from .models import Payment


class PaymentRepository:
    @staticmethod
    def get_active_by_order(order):
        return Payment.objects.filter(
            order=order, status__in=[Payment.Status.CREATED, Payment.Status.PENDING]
        ).first()

    @staticmethod
    def get_active_for_update_by_order(order):
        return (
            Payment.objects.select_for_update()
            .filter(
                order=order, status__in=[Payment.Status.CREATED, Payment.Status.PENDING]
            )
            .first()
        )

    @staticmethod
    def create_payment(order):
        return Payment.objects.create(order=order, amount=order.total)

    @staticmethod
    def get_for_update(payment_id):
        return Payment.objects.select_for_update().get(id=payment_id)

    @staticmethod
    def get_latest_by_order_or_raise(order):
        payment = Payment.objects.filter(order=order).order_by("-created_at").first()

        if payment is None:
            raise PaymentNotFoundError(
                "Nenhum Pix ativo foi encontrado para este pedido"
            )

        return payment

    @staticmethod
    def get_by_provider_payment_id(provider_payment_id):
        try:
            return Payment.objects.select_for_update().get(
                mercado_pago_payment_id=provider_payment_id
            )
        except Payment.DoesNotExist:
            raise PaymentNotFoundError(
                f"Nenhum pagamento encontrado para este payment_id: {provider_payment_id}"
            )
