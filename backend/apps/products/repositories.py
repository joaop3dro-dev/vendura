from django.db.models import F

from .exceptions import InvalidProductError
from .models import Product


class ProductRepository:
    @staticmethod
    def get_products_for_update(product_ids: list):
        products = (
            Product.objects.select_for_update()
            .filter(id__in=product_ids, public=True)
            .order_by("id")
            .in_bulk()
        )

        if set(product_ids) - set(products):
            raise InvalidProductError("O produto enviado é inválido")

        return products

    @staticmethod
    def decrement_stock(product_id: int, quantity: int):
        Product.objects.filter(id=product_id, stock__gte=quantity).update(
            stock=F("stock") - quantity
        )

    @staticmethod
    def get_by_id(id):
        product = Product.objects.get(pk=id)
        return product

    @staticmethod
    def get_product_for_update_direct(product_id):
        try:
            return (
                Product.objects.select_for_update()
                .filter(public=True)
                .get(id=product_id)
            )
        except Product.DoesNotExist:
            raise InvalidProductError("o produto enviado é inválido")

    @staticmethod
    def increment_stock(product_id, quantity):
        Product.objects.filter(id=product_id).update(stock=F("stock") + quantity)
