from django.core.management.base import BaseCommand

from apps.orders.repositories import OrderRepository
from apps.payment.services import PaymentService


class Command(BaseCommand):
    help = "Expira pedidos pendentes cujo prazo de pagamento venceu."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **kwargs):
        order_ids = OrderRepository.get_expired_pending_orders_ids(
            limit=kwargs["limit"]
        )

        expired_orders_count = 0

        for order_id in order_ids:
            order = PaymentService.expire_order(order_id)

            if order is not None:
                expired_orders_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{expired_orders_count} pedidos pendentes foram expirados com sucesso."
            )
        )
