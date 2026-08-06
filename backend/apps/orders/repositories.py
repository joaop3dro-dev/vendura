from .exceptions import OrderNotFoundError
from .models import Order, OrderItem


class OrderRepository:
    @staticmethod
    def get_order_for_update(customer, order_id):
        try:
            return Order.objects.select_for_update().get(
                pk=order_id,
                customer=customer,
            )
        except Order.DoesNotExist:
            raise OrderNotFoundError(
                f"Nenhum pedido foi encontrado com o id {order_id}"
            )

    @staticmethod
    def cancel_order(order: Order):
        order.cancel()

        return order

    @staticmethod
    def create_new_order(
        customer, total, delivery_address, coupon=None, status=Order.Status.PENDING
    ):
        return Order.objects.create(
            customer=customer,
            total=total,
            delivery_address=delivery_address,
            status=status,
            coupon=coupon,
        )


class OrderItemRepository:
    @staticmethod
    def get_order_items(order_id):
        return OrderItem.objects.filter(
            order_id=order_id,
        ).select_related("product")

    @staticmethod
    def create_order_item(order, product, quantity, unit_price):
        return OrderItem.objects.create(
            order=order, product=product, quantity=quantity, unit_price=unit_price
        )
