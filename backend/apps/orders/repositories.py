from .exceptions import OrderNotExists
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
            raise OrderNotExists(f"Nenhum pedido foi encontrado com o id {order_id}")

    @staticmethod
    def cancel_order(order: Order):
        order.cancel()

        return order

    @staticmethod
    def create_new_order(customer, total, status=Order.Status.PENDING):
        return Order.objects.create(customer=customer, total=total, status=status)


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
