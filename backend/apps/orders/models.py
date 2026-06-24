from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q

from apps.coupons.models import Coupon
from apps.products.models import Product

User = get_user_model()


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PAID = "paid", "Pago"
        SHIPPED = "shipped", "Enviado"
        DELIVERED = "delivered", "Entregue"
        CANCELLED = "cancelled", "Cancelado"
        PROCESSING = "processing", "Processando"

    customer = models.ForeignKey(User, on_delete=models.PROTECT)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    coupon = models.ForeignKey(
        Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(total__gt=0), name="total_price_positive"
            )
        ]
        permissions = [
            ("cancel_order", "Can cancel order"),
            ("approve_order", "Can approve order"),
        ]

    def __str__(self):
        return f"Order #{self.pk} - {self.status}"

    def cancel(self):
        if self.status not in [
            self.Status.PENDING,
            self.Status.PAID,
        ]:
            raise ValueError(
                f"Pedido com status '{self.status}' não pode ser cancelado"
            )
        self.status = self.Status.CANCELLED
        self.save(update_fields=["status"])

    def approve(self):
        if self.status != self.Status.PENDING:
            raise ValueError(f"Pedido com status '{self.status}' não pode ser aprovado")

        self.status = self.Status.PAID
        self.save(update_fields=["status"])


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
                condition=Q(unit_price__gt=0), name="orderitem_unit_price_positive"
            ),
            models.CheckConstraint(
                condition=Q(quantity__gt=0), name="orderitem_quantity_positive"
            ),
        ]
