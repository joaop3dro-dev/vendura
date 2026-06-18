from django.db.models import F

from .models import Product


class ProductRepository:
    @staticmethod
    def get_products_for_update(product_ids: list):
        return (
            Product.objects.select_for_update()
            .filter(id__in=product_ids)
            .order_by("id")
            .in_bulk()
        )

    @staticmethod
    def decrement_stock(product_id: int, quantity: int):
        Product.objects.filter(id=product_id).update(stock=F("stock") - quantity)
