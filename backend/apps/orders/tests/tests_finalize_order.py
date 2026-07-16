from datetime import timedelta
from decimal import Decimal

from django.db.models import Prefetch
from django.test import TestCase
from django.utils import timezone

from apps.coupons.exceptions import (
    CouponExpiredError,
    CouponMinimumOrderValueError,
    CouponNotActivatedError,
    CouponNotFoundError,
    CouponUsageLimitReachedError,
)
from apps.coupons.factory import CouponFactory
from apps.coupons.repositories import CouponRepository
from apps.products.factory import CategoryFactory, ProductFactory
from apps.products.models import Product
from apps.users.factory import UserFactory

from ..models import Order, OrderItem
from ..services import finalize_order


class FinalizeOrderTest(TestCase):
    def setUp(self):
        self.customer = UserFactory()
        self.category = CategoryFactory()
        self.product = ProductFactory(category=self.category)
        self.coupon = CouponFactory()

        self.itens = [{"product": self.product.id, "quantity": 1}]

    def test_finalize_order_with_coupon(self):
        products = ProductFactory.create_batch(5, category=self.category)
        product_stock_before = [{"product": p.id, "stock": p.stock} for p in products]

        itens = [{"product": product.id, "quantity": 1} for product in products]

        order_id = finalize_order(
            customer=self.customer, itens=itens, cupom_code=self.coupon.code
        )

        order = Order.objects.prefetch_related(
            Prefetch("items", queryset=OrderItem.objects.select_related("product"))
        ).get(pk=order_id)

        expected_price_without_coupon = Decimal(str(sum([p.price for p in products])))

        discount = expected_price_without_coupon * (self.coupon.discount_percent / 100)

        if self.coupon.max_discount_amount is not None:
            discount = min(discount, self.coupon.max_discount_amount)

        expected_price_with_coupon = expected_price_without_coupon - discount

        self.assertEqual(order.total, expected_price_with_coupon)
        self.assertEqual(order.status, Order.Status.PENDING)

        coupon = CouponRepository.get_coupon(self.coupon.code)

        self.assertEqual(coupon.used, (self.coupon.used + 1))

        db_product_ids = [item.product.id for item in order.items.all()]

        expected_products_ids = [p.id for p in products]

        self.assertEqual(db_product_ids, expected_products_ids)

        orderitems = [
            {"product": item.product.id, "quantity": item.quantity}
            for item in order.items.all()
        ]

        orderitems_map = {oi["product"]: oi["quantity"] for oi in orderitems}

        for item in itens:
            self.assertEqual(orderitems_map[item["product"]], item["quantity"])

        products_for_validation = Product.objects.in_bulk(db_product_ids)

        for p in product_stock_before:
            product = products_for_validation[p["product"]]
            quantity = orderitems_map[p["product"]]

            self.assertEqual(product.stock, (p["stock"] - quantity))

    def test_finalize_order_without_coupon(self):
        products = ProductFactory.create_batch(5, category=self.category)
        product_stock_before = [{"product": p.id, "stock": p.stock} for p in products]

        itens = [{"product": product.id, "quantity": 1} for product in products]
        order_id = finalize_order(customer=self.customer, itens=itens)

        order = Order.objects.prefetch_related(
            Prefetch("items", queryset=OrderItem.objects.select_related("product"))
        ).get(pk=order_id)

        expected_price = Decimal(str(sum([p.price for p in products])))
        self.assertEqual(order.total, expected_price)

        self.assertEqual(order.status, Order.Status.PENDING)

        db_product_ids = [item.product.id for item in order.items.all()]

        expected_products_ids = [p.id for p in products]

        self.assertEqual(db_product_ids, expected_products_ids)

        orderitems = [
            {"product": item.product.id, "quantity": item.quantity}
            for item in order.items.all()
        ]

        orderitems_map = {oi["product"]: oi["quantity"] for oi in orderitems}

        for item in itens:
            self.assertEqual(orderitems_map[item["product"]], item["quantity"])

        products_for_validation = Product.objects.in_bulk(db_product_ids)

        for p in product_stock_before:
            product = products_for_validation[p["product"]]
            quantity = orderitems_map[p["product"]]

            self.assertEqual(product.stock, (p["stock"] - quantity))

    def test_finalize_order_insufficient_stock(self):
        itens = [{"product": self.product.id, "quantity": self.product.stock + 1}]

        with self.assertRaises(ValueError):
            finalize_order(customer=self.customer, itens=itens)

    def test_coupon_usage_limit_reached(self):
        coupon = CouponFactory(used=10, uses=10)

        with self.assertRaises(CouponUsageLimitReachedError):
            finalize_order(
                customer=self.customer, itens=self.itens, cupom_code=coupon.code
            )

    def test_coupon_not_found(self):

        with self.assertRaises(CouponNotFoundError):
            finalize_order(
                customer=self.customer, itens=self.itens, cupom_code="INVALID_CODE"
            )

    def test_coupon_not_activated(self):
        coupon = CouponFactory(activated=False)

        with self.assertRaises(CouponNotActivatedError):
            finalize_order(
                customer=self.customer, itens=self.itens, cupom_code=coupon.code
            )

    def test_coupon_expired(self):
        coupon = CouponFactory(expires=(timezone.now() - timedelta(days=1)))

        with self.assertRaises(CouponExpiredError):
            finalize_order(
                customer=self.customer, itens=self.itens, cupom_code=coupon.code
            )

    def test_coupon_min_order_value_error(self):
        coupon = CouponFactory(min_value_amount=(self.product.price + Decimal(10)))

        with self.assertRaises(CouponMinimumOrderValueError):
            finalize_order(
                customer=self.customer, itens=self.itens, cupom_code=coupon.code
            )
