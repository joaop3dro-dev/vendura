from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from coupon import (
    CouponExpiredError,
    CouponMinimumOrderValueError,
    CouponNotActivatedError,
    CouponNotFoundError,
    CouponRepository,
    CouponUsageLimitReachedError,
)
from product import ProductRepository

from .models import Coupon, Order
from .repositorys import OrderItemRepository, OrderRepository

itens = [{"product": 1, "quantity": 5}]


def calc_total(itens, products):
    total = Decimal("0")

    for item in itens:
        product = products[item["product"]]
        total += product.price * item["quantity"]
    return total


@transaction.atomic
def finalize_order(customer, itens, cupom_code=None):
    products_ids = [item["product"] for item in itens]
    products = ProductRepository.get_products_for_update(products_ids)

    total = calc_total(itens, products)
    if cupom_code:
        try:
            coupon = CouponRepository.get_coupon(cupom_code)
        except Coupon.DoesNotExist:
            raise CouponNotFoundError(f"Cupom '{cupom_code}' não encontrado")

        discount_percent = coupon.discount_percent

        if not coupon.activated:
            raise CouponNotActivatedError(
                f"Cupom '{cupom_code}' não está ativado para uso"
            )

        if coupon.expires < timezone.now():
            raise CouponExpiredError("Cupom expirado")

        if coupon.min_value_amount is not None and total < coupon.min_value_amount:
            raise CouponMinimumOrderValueError("Valor mínimo de uso não atingido")

        discount = total * (discount_percent / 100)

        if coupon.max_discount_amount is not None:
            discount = min(discount, coupon.max_discount_amount)
        total -= discount

        updated = CouponRepository.coupon_add_use(coupon.id)

        if updated == 0:
            raise CouponUsageLimitReachedError("Limite de usos atingido")

    for item in itens:
        product = products[item["product"]]

        if product.stock < item["quantity"]:
            raise ValueError(f"Estoque insuficiente para {product.name}")

    order = OrderRepository.create_new_order(customer, total)

    for item in itens:
        product = products[item["product"]]

        OrderItemRepository.create_order_item(
            order, product, item["quantity"], unit_price=product.price
        )

        ProductRepository.decrement_stock(product.id, item["quantity"])

    return order


@transaction.atomic
def apply_discount_coupon(code, order_id):
    order = Order.objects.get(id=order_id)
    value_total = order.total

    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        raise CouponNotFoundError(f"Cupom {code} não encontrado")

    discount_percent = coupon.discount_percent

    if not coupon.activated:
        raise CouponNotActivatedError(f"Cupom {code} não está ativado para uso")

    if coupon.expires < timezone.now():
        raise CouponExpiredError("Cupom expirado")

    if coupon.min_value_amount is not None and value_total < coupon.min_value_amount:
        raise CouponMinimumOrderValueError("Valor mínimo de uso não atingido")

    updated = Coupon.objects.filter(id=coupon.id, used__lt=F("uses")).update(
        used=F("used") + 1
    )
    if updated == 0:
        raise CouponUsageLimitReachedError("Limite de usos atingido")

    discount = value_total * (discount_percent / 100)

    if coupon.max_discount_amount is not None:
        discount = min(discount, coupon.max_discount_amount)

    Order.objects.filter(id=order.id).update(total=F("total") - discount)


@transaction.atomic
def order_pedding_process():
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
