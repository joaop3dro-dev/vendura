from rest_framework import status
from rest_framework.test import APITestCase

from apps.coupons.factory import CouponFactory
from apps.products.factory import CategoryFactory, ProductFactory
from apps.users.factory import UserFactory


class FinalizeOrderAPITest(APITestCase):
    def setUp(self):
        self.customer = UserFactory()
        self.product = ProductFactory()
        self.category = CategoryFactory()
        self.coupon = CouponFactory()

        self.payload = {"itens": [{"product": self.product.id, "quantity": 1}]}
        self.url = "/api/orders/finalize/"

    def test_finalize_order_requires_authentication(self):

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_finalize_order_success(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.post(self.url, self.payload, format="json")

    def test_finalize_order_invalid_coupon(self):
        self.client.force_authenticate(user=self.customer)

        self.payload.update(cupom_code='INVALID_CODE')

        response = self.client.post(
            self.url, self.payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["code"], "CouponNotFoundError")
