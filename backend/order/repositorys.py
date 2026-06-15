from .models import Order, OrderItem


class OrderRepository:
    @staticmethod
    def create_new_order(customer, total, status=Order.Status.PENDING):
        return Order.objects.create(customer=customer, total=total, status=status)


class OrderItemRepository:
    @staticmethod
    def create_order_item(order, product, quantity, unit_price):
        return OrderItem.objects.create(
            order=order, product=product, quantity=quantity, unit_price=unit_price
        )
