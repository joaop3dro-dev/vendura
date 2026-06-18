from django.db import models
from django.db.models import F, Q


# Create your models here.
class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.DecimalField(decimal_places=2, max_digits=5)
    max_discount_amount = models.DecimalField(
        decimal_places=2, max_digits=10, null=True, blank=True
    )
    uses = models.PositiveIntegerField()
    used = models.PositiveIntegerField()
    min_value_amount = models.DecimalField(
        decimal_places=2, max_digits=10, blank=True, null=True
    )
    activated = models.BooleanField(default=True)
    expires = models.DateTimeField()

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(uses__gt=0), name="cupom_uses_positive"),
            models.CheckConstraint(
                condition=Q(used__lte=F("uses")), name="coupon_used_lte_uses"
            ),
        ]
