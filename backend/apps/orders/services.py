from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.carts.exceptions import EmptyCartError
from apps.carts.repositories import CartItemRepository
from apps.coupons.exceptions import (
    CouponExpiredError,
    CouponMinimumOrderValueError,
    CouponNotActivatedError,
    CouponNotFoundError,
    CouponUsageLimitReachedError,
)
from apps.coupons.repositories import CouponRepository
from apps.customers.repositories import AddressRepository
from apps.products.exceptions import InsufficientStockError, InvalidProductError
from apps.products.repositories import ProductRepository

from .models import Coupon, Order
from .repositories import OrderItemRepository, OrderRepository


def calc_total(items, products):
    total = Decimal("0")

    for item, qty in items:
        product = products[item]
        total += product.price * qty
    return total


@transaction.atomic
def finalize_direct_order(customer, coupon_code, item, address_id):
    delivery_address = AddressRepository.get_address_by_id(customer, address_id)
    product = ProductRepository.get_products_for_update_direct(item["product"].id)

    total = product.price * item["quantity"]

    if coupon_code:
        try:
            coupon = CouponRepository.get_coupon(coupon_code)
        except Coupon.DoesNotExist:
            raise CouponNotFoundError(f"Cupom '{coupon_code}' não encontrado")

        discount_percent = coupon.discount_percent

        if not coupon.activated:
            raise CouponNotActivatedError(
                f"Cupom '{coupon_code}' não está ativado para uso"
            )

        if coupon.expires < timezone.now():
            raise CouponExpiredError("Cupom expirado")

        if coupon.min_value_amount is not None and total < coupon.min_value_amount:
            raise CouponMinimumOrderValueError("Valor mínimo de uso não atingido")

        discount = total * (discount_percent / Decimal(100))

        if coupon.max_discount_amount is not None:
            discount = min(discount, coupon.max_discount_amount)
        total -= discount

        updated = CouponRepository.increment_usage(coupon.id)

        if updated == 0:
            raise CouponUsageLimitReachedError("Limite de usos atingido")

    if product.stock < item["quantity"]:
        raise InsufficientStockError(f"Estoque insuficiente para {product.name}")

    order = OrderRepository.create_new_order(customer, total, delivery_address)

    OrderItemRepository.create_order_item(
        order, product, item["quantity"], unit_price=product.price
    )

    ProductRepository.decrement_stock(product.id, item["quantity"])

    return order.pk


@transaction.atomic
def finalize_order_cart(customer, coupon_code, address_id):
    delivery_address = AddressRepository.get_address_by_id(customer, address_id)
    items = CartItemRepository.get_customer_cart_items_tuple(customer)

    if len(items) == 0:
        raise EmptyCartError("Não há produtos selecionados no carrinho")

    product_ids = [item_id for item_id, _ in items]
    products = ProductRepository.get_products_for_update(product_ids)

    if len(products) != len(set(product_ids)):
        raise InvalidProductError("Produto inválido no carrinho")

    total = calc_total(items, products)
    if coupon_code:
        try:
            coupon = CouponRepository.get_coupon(coupon_code)
        except Coupon.DoesNotExist:
            raise CouponNotFoundError(f"Cupom '{coupon_code}' não encontrado")

        discount_percent = coupon.discount_percent

        if not coupon.activated:
            raise CouponNotActivatedError(
                f"Cupom '{coupon_code}' não está ativado para uso"
            )

        if coupon.expires < timezone.now():
            raise CouponExpiredError("Cupom expirado")

        if coupon.min_value_amount is not None and total < coupon.min_value_amount:
            raise CouponMinimumOrderValueError("Valor mínimo de uso não atingido")

        discount = total * (discount_percent / Decimal(100))

        if coupon.max_discount_amount is not None:
            discount = min(discount, coupon.max_discount_amount)
        total -= discount

        updated = CouponRepository.increment_usage(coupon.id)

        if updated == 0:
            raise CouponUsageLimitReachedError("Limite de usos atingido")

    for item, qty in items:
        product = products[item]

        if product.stock < qty:
            raise InsufficientStockError(f"Estoque insuficiente para {product.name}")

    order = OrderRepository.create_new_order(customer, total, delivery_address)

    for item, qty in items:
        product = products[item]

        OrderItemRepository.create_order_item(
            order, product, qty, unit_price=product.price
        )

        ProductRepository.decrement_stock(product.id, qty)

    CartItemRepository.delete_customer_cart_items(customer)

    return order.pk


@transaction.atomic
def order_pending_process():
    order = (
        Order.objects.select_for_update(skip_locked=True)
        .filter(status=Order.Status.PENDING)
        .order_by("created_at")
        .first()
    )

    if order is None:
        return None

    order.status = Order.Status.PROCESSING
    order.save()

    return order


@transaction.atomic
def cancel_order(customer, order_id):
    order = OrderRepository.get_order_for_update(customer, order_id)

    order_items = OrderItemRepository.get_order_items(order_id)

    order = OrderRepository.cancel_order(order=order)

    for order_item in order_items:
        ProductRepository.increment_stock(
            product_id=order_item.product.id, quantity=order_item.quantity
        )

    return order
