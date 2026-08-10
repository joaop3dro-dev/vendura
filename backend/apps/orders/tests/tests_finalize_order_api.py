from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from apps.carts.models import Cart, CartItem
from apps.customers.factory import AddressFactory, CustomerFactory
from apps.products.factory import ProductFactory

from ..models import Order


class CreateOrderAPITest(APITestCase):
    def setUp(self):
        self.customer = CustomerFactory()
        self.user = self.customer.user
        self.address = AddressFactory(customer=self.customer)
        self.product = ProductFactory(stock=10)
        self.direct_payload = {
            "item": {"product": self.product.id, "quantity": 1},
            "address_id": self.address.id,
        }

    def test_create_order_requires_authentication(self):
        response = self.client.post(
            "/api/orders/finalize-direct/", self.direct_payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_direct_order(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/orders/finalize-direct/", self.direct_payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["items"][0]["product"], self.product.id)

    def test_create_cart_order(self):
        self.client.force_authenticate(user=self.user)
        cart = Cart.objects.create(customer=self.customer)
        CartItem.objects.create(cart=cart, item=self.product, quantity=2)

        response = self.client.post(
            "/api/orders/finalize-cart/",
            {"address_id": self.address.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["items"][0]["quantity"], 2)

    def test_cancel_order_restores_stock(self):
        self.client.force_authenticate(user=self.user)
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
        other_customer = CustomerFactory()
        self.client.force_authenticate(user=other_customer.user)
        order = Order.objects.create(
            customer=self.customer,
            total=self.product.price,
        )

        response = self.client.post(f"/api/orders/{order.pk}/cancel/", format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_cart_returns_400_for_empty_cart(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/orders/finalize-cart/",
            {"address_id": self.address.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "EmptyCartError")

    def test_create_cart_returns_400_for_invalid_product(self):
        self.client.force_authenticate(user=self.user)
        cart = Cart.objects.create(customer=self.customer)
        CartItem.objects.create(cart=cart, item=self.product, quantity=1)

        with patch(
            "apps.orders.services.ProductRepository.get_products_for_update",
            return_value={},
        ):
            response = self.client.post(
                "/api/orders/finalize-cart/",
                {"address_id": self.address.id},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "InvalidProductError")

    def test_create_direct_returns_409_for_insufficient_stock(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "item": {"product": self.product.id, "quantity": 11},
            "address_id": self.address.id,
        }

        response = self.client.post(
            "/api/orders/finalize-direct/",
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "InsufficientStockError")
