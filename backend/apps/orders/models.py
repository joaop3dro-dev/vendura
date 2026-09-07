from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.coupons.models import Coupon
from apps.customers.models import Customer
from apps.products.models import Product

from .exceptions import OrderCannotBeCancelledError


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PAID = "paid", "Pago"
        SHIPPED = "shipped", "Enviado"
        DELIVERED = "delivered", "Entregue"
        CANCELLED = "cancelled", "Cancelado"
        PROCESSING = "processing", "Processando"
        EXPIRED = "expired", "Expirado"

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    coupon = models.ForeignKey(
        Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    delivery_address = models.JSONField(default=dict)
    expires_at = models.DateTimeField()
    expired_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

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
        if self.status != self.Status.PENDING:
            raise OrderCannotBeCancelledError(
                f"Pedido com status '{self.status}' não pode ser cancelado"
            )
        self.status = self.Status.CANCELLED
        self.cancelled_at = timezone.now()
        self.save(update_fields=["status", "cancelled_at"])

    def expire(self):
        now = timezone.now()
        if self.status != self.Status.PENDING:
            return False

        if self.expires_at > now:
            return False

        self.status = self.Status.EXPIRED
        self.expired_at = now
        self.save(update_fields=["status", "expired_at"])
        return True

    def approve(self):
        if self.status != self.Status.PENDING:
            raise ValueError(f"Pedido com status '{self.status}' não pode ser aprovado")
        self.paid_at = timezone.now()
        self.status = self.Status.PAID
        self.save(update_fields=["status", "paid_at"])


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
