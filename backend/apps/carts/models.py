from django.db import models
from django.db.models import Q

from apps.customers.models import Customer
from apps.products.models import Product


class Cart(models.Model):
    customer = models.OneToOneField(
        Customer, on_delete=models.CASCADE, related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    class SelectedChoices(models.TextChoices):
        SELECTED = "selected", "Selecionado"
        UNSELECTED = "unselected", "Não Selecionado"

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="carts")
    quantity = models.PositiveIntegerField(default=1)
    selected = models.CharField(
        choices=SelectedChoices.choices,
        default=SelectedChoices.SELECTED,
        db_index=True,
        max_length=20,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0), name="quantity_greater_than_zero"
            ),
            models.UniqueConstraint(
                fields=["cart", "item"], name="unique_product_per_cart"
            ),
        ]
