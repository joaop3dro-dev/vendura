import logging
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
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

from .models import Coupon
from .repositories import OrderItemRepository, OrderRepository

logger = logging.getLogger(__name__)


class OrderService:
    @staticmethod
    def calc_total(items, products):
        total = Decimal("0")

        for item, qty in items:
            product = products[item]
            total += product.price * qty
        return total

    @staticmethod
    @transaction.atomic
    def create_direct_order(customer, coupon_code, item, address_id):
        logger.info("service chamado")
        delivery_address = AddressRepository.get_address_by_id(customer, address_id)
        product = ProductRepository.get_product_for_update_direct(item["product"].id)

        total = product.price * item["quantity"]

        coupon, total = OrderService.apply_coupon(coupon_code, total)

        if product.stock < item["quantity"]:
            raise InsufficientStockError(f"Estoque insuficiente para {product.name}")

        logger.info("produto e quantidade válidos")
        expires_at = OrderService.get_order_expiration()

        order = OrderRepository.create_new_order(
            customer=customer,
            total=total,
            delivery_address=delivery_address,
            expires_at=expires_at,
            coupon=coupon,
        )

        OrderItemRepository.create_order_item(
            order=order,
            product=product,
            quantity=item["quantity"],
            unit_price=product.price,
        )

        ProductRepository.decrement_stock(
            product_id=product.id,
            quantity=item["quantity"],
        )

        logger.info("pedido criado com sucesso. order_id: %s", order.pk)

        return order.pk

    @staticmethod
    @transaction.atomic
    def create_order_cart(customer, coupon_code, address_id):
        logger.info("service chamado")
        delivery_address = AddressRepository.get_address_by_id(customer, address_id)
        items = CartItemRepository.get_customer_cart_items_tuple(customer)

        if len(items) == 0:
            raise EmptyCartError("Não há produtos selecionados no carrinho")

        product_ids = [item_id for item_id, _ in items]
        products = ProductRepository.get_products_for_update(product_ids)

        if len(products) != len(set(product_ids)):
            raise InvalidProductError("Produto inválido no carrinho")

        for item, qty in items:
            product = products[item]

            if product.stock < qty:
                raise InsufficientStockError(
                    f"Estoque insuficiente para {product.name}"
                )

        logger.info("produtos e quantidade válidos")

        total = OrderService.calc_total(items, products)

        coupon, total = OrderService.apply_coupon(coupon_code, total)

        expires_at = OrderService.get_order_expiration()

        order = OrderRepository.create_new_order(
            customer=customer,
            total=total,
            delivery_address=delivery_address,
            expires_at=expires_at,
            coupon=coupon,
        )

        for item, qty in items:
            product = products[item]

            OrderItemRepository.create_order_item(
                order, product, qty, unit_price=product.price
            )

            ProductRepository.decrement_stock(product.id, qty)

        CartItemRepository.delete_customer_cart_items(customer)

        logger.info("pedido criado com sucesso. order_id: %s", order.pk)

        return order.pk

    @staticmethod
    @transaction.atomic
    def cancel_order(customer, order_id):
        order = OrderRepository.get_order_for_update(customer, order_id)

        order.cancel()
        OrderService._release_order_reservations(order)
        return order

    @staticmethod
    def apply_coupon(coupon_code, total):
        if coupon_code:
            try:
                coupon = CouponRepository.get_coupon(coupon_code)
            except Coupon.DoesNotExist:
                logger.warning("cupom não encontrado. coupom_code: %s", coupon_code)
                raise CouponNotFoundError(f"Cupom '{coupon_code}' não encontrado")

            discount_percent = coupon.discount_percent

            if not coupon.activated:
                logger.warning("cupom não ativado. coupon_code: %s", coupon_code)
                raise CouponNotActivatedError(
                    f"Cupom '{coupon_code}' não está ativado para uso"
                )

            if coupon.expires < timezone.now():
                logger.warning("cupom expirado. coupon_code: %s", coupon_code)
                raise CouponExpiredError("Cupom expirado")

            if coupon.min_value_amount is not None and total < coupon.min_value_amount:
                logger.warning(
                    "valor mínimo de compra não atingido. coupon_code: %s", coupon_code
                )
                raise CouponMinimumOrderValueError("Valor mínimo de uso não atingido")

            discount = total * (discount_percent / Decimal(100))

            if coupon.max_discount_amount is not None:
                discount = min(discount, coupon.max_discount_amount)
            total -= discount

            updated = CouponRepository.increment_usage(coupon.id)

            if updated == 0:
                logger.warning(
                    "limite de usos do cupom atingido. coupon_code: %s", coupon_code
                )
                raise CouponUsageLimitReachedError("Limite de usos atingido")

            return coupon, total
        else:
            return None, total

    @staticmethod
    def get_order_expiration():
        return timezone.now() + timedelta(
            minutes=settings.ORDER_PAYMENT_EXPIRATION_MINUTES
        )

    @staticmethod
    def _release_order_reservations(order):
        order_items = OrderItemRepository.get_order_items(order.id)

        for order_item in order_items:
            ProductRepository.increment_stock(
                product_id=order_item.product_id,
                quantity=order_item.quantity,
            )

        if order.coupon_id:
            CouponRepository.decrement_usage(order.coupon_id)

    @staticmethod
    @transaction.atomic
    def expire_order(order_id):
        order = OrderRepository.get_order_for_update_by_id(order_id)

        expired = order.expire()

        if not expired:
            return None

        OrderService._release_order_reservations(order)

        return order
