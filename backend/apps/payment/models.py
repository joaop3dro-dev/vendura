from uuid import uuid4

from django.db import models
from django.db.models import Q

from apps.orders.models import Order


class Payment(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Criado"
        PENDING = "pending", "Pendente"
        APPROVED = "approved", "Aprovado"
        REJECTED = "rejected", "Rejeitado"
        CANCELED = "canceled", "Cancelado"
        EXPIRED = "expired", "Expirado"
        ERROR = "error", "Erro de integração"

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CREATED, db_index=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    idempotency_key = models.UUIDField(default=uuid4, unique=True, editable=False)
    cancel_idempotency_key = models.UUIDField(
        unique=True, editable=False, blank=True, null=True
    )
    external_reference = models.UUIDField(default=uuid4, unique=True, editable=False)

    mercado_pago_order_id = models.CharField(
        max_length=64, unique=True, blank=True, null=True
    )
    mercado_pago_payment_id = models.CharField(
        max_length=100, unique=True, blank=True, null=True
    )
    provider_status = models.CharField(max_length=50, blank=True)
    provider_status_detail = models.CharField(max_length=100, blank=True)

    pix_copy_paste = models.TextField(blank=True)
    ticket_url = models.URLField(max_length=2048, blank=True)

    last_error = models.TextField(blank=True)
    approved_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order"],
                condition=Q(status__in=["created", "pending"]),
                name="one_active_payment_per_order",
            ),
            models.CheckConstraint(
                condition=Q(amount__gt=0), name="payment_amount_positive"
            ),
        ]

    def __str__(self):
        return f"Payment for Order {self.order.id} - Status: {self.status}"
