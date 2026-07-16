from datetime import timedelta
from decimal import Decimal

import factory
from django.utils import timezone

from .models import Coupon


class CouponFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Coupon

    code = factory.Sequence(lambda n: f"ABC_{n}")
    discount_percent = Decimal(10)
    max_discount_amount = Decimal(60)
    uses = 10
    used = 0
    min_value_amount = Decimal(100)
    expires = factory.LazyFunction(lambda: timezone.now() + timedelta(days=30))
    activated = True
