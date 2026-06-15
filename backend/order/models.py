from django.db import models
from models import Q

from ..coupon.models import Coupon
from ..product.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PAID = "paid", "Pago"
        SHIPPED = "shipped", "Enviado"
        DELIVERED = "delivered", "Entregue"
        CANCELLED = "cancelled", "Cancelado"
        PROCESSING = "processing", "Processando"

    customer = models.ForeignKey("Custome", on_delete=models.PROTECT)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    coupon = models.ForeignKey(Coupon, on_delete="")

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(total__gt=0), name="total_price_positive")
        ]

    def __str__(self):
        return f"Order #{self.pk} - {self.status}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(unit_price__gt=0), name="orderitem_unit_price_positive"
            ),
            models.CheckConstraint(
                check=Q(quantity__gt=0), name="orderitem_quantity_positive"
            ),
        ]
