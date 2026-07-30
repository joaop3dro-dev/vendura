from rest_framework import status
from rest_framework.test import APITestCase

from apps.carts.models import Cart, CartItem
from apps.products.factory import ProductFactory
from apps.users.factory import UserFactory

from ..models import Order


class FinalizeOrderAPITest(APITestCase):
    def setUp(self):
        self.customer = UserFactory()
        self.product = ProductFactory(stock=10)
        self.direct_payload = {
            "item": {"product": self.product.id, "quantity": 1}
        }

    def test_finalize_order_requires_authentication(self):
        response = self.client.post(
            "/api/orders/finalize-direct/", self.direct_payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_finalize_direct_order(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(
            "/api/orders/finalize-direct/", self.direct_payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["items"][0]["product"], self.product.id)

    def test_finalize_cart_order(self):
        self.client.force_authenticate(user=self.customer)
        cart = Cart.objects.create(customer=self.customer)
        CartItem.objects.create(cart=cart, item=self.product, quantity=2)

        response = self.client.post("/api/orders/finalize-cart/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["items"][0]["quantity"], 2)

    def test_cancel_order_restores_stock(self):
        self.client.force_authenticate(user=self.customer)
        order_response = self.client.post(
            "/api/orders/finalize-direct/", self.direct_payload, format="json"
        )
        order_id = order_response.data["id"]

        response = self.client.post(f"/api/orders/{order_id}/cancel/", format="json")

        self.product.refresh_from_db()
        order = Order.objects.get(pk=order_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(self.product.stock, 10)

    def test_customer_cannot_cancel_another_customers_order(self):
        other_customer = UserFactory()
        self.client.force_authenticate(user=other_customer)
        order = Order.objects.create(
            customer=self.customer,
            total=self.product.price,
        )

        response = self.client.post(f"/api/orders/{order.pk}/cancel/", format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
