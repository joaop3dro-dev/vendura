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
