from decimal import Decimal

from django.test import TestCase

from apps.carts.models import Cart, CartItem
from apps.coupons.factory import CouponFactory
from apps.products.factory import ProductFactory
from apps.users.factory import UserFactory

from ..models import Order
from ..services import finalize_direct_order, finalize_order_cart


class FinalizeOrderTest(TestCase):
    def setUp(self):
        self.customer = UserFactory()
        self.product = ProductFactory(price=Decimal("100.00"), stock=10)

    def test_finalize_direct_order(self):
        order_id = finalize_direct_order(
            customer=self.customer,
            coupon_code=None,
            item={"product": self.product, "quantity": 2},
        )

        order = Order.objects.prefetch_related("items").get(pk=order_id)
        self.product.refresh_from_db()

        self.assertEqual(order.total, Decimal("200.00"))
        self.assertEqual(order.items.get().quantity, 2)
        self.assertEqual(self.product.stock, 8)

    def test_finalize_direct_order_with_coupon(self):
        coupon = CouponFactory(
            discount_percent=Decimal("10.00"),
            min_value_amount=Decimal("0.00"),
        )
        order_id = finalize_direct_order(
            customer=self.customer,
            coupon_code=coupon.code,
            item={"product": self.product, "quantity": 1},
        )

        order = Order.objects.get(pk=order_id)
        coupon.refresh_from_db()

        self.assertEqual(order.total, Decimal("90.00"))
        self.assertEqual(coupon.used, 1)

    def test_finalize_cart_uses_only_selected_items(self):
        cart = Cart.objects.create(customer=self.customer)
        unselected_product = ProductFactory(stock=10)
        CartItem.objects.create(cart=cart, item=self.product, quantity=2)
        CartItem.objects.create(
            cart=cart,
            item=unselected_product,
            quantity=1,
            selected=CartItem.SelectedChoices.NO_SELECTED,
        )

        order_id = finalize_order_cart(customer=self.customer, coupon_code=None)

        order = Order.objects.prefetch_related("items").get(pk=order_id)
        self.product.refresh_from_db()
        unselected_product.refresh_from_db()

        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.get().product, self.product)
        self.assertEqual(self.product.stock, 8)
        self.assertEqual(unselected_product.stock, 10)
        self.assertFalse(CartItem.objects.filter(cart=cart, item=self.product).exists())
        self.assertTrue(
            CartItem.objects.filter(cart=cart, item=unselected_product).exists()
        )

    def test_finalize_direct_order_rejects_insufficient_stock(self):
        with self.assertRaises(ValueError):
            finalize_direct_order(
                customer=self.customer,
                coupon_code=None,
                item={"product": self.product, "quantity": 11},
            )

        self.assertFalse(Order.objects.exists())
