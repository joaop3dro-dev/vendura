from django.db.models import F
from django.utils import timezone

from .models import Coupon


class CouponRepository:
    @staticmethod
    def get_coupon(code):
        return Coupon.objects.get(code=code)

    @staticmethod
    def increment_usage(coupon_id):
        return Coupon.objects.filter(
            id=coupon_id, used__lt=F("uses"), activated=True, expires__gt=timezone.now()
        ).update(used=F("used") + 1)

    @staticmethod
    def decrement_usage(coupon_id):
        return Coupon.objects.filter(id=coupon_id, used__gt=0).update(
            used=F("used") - 1
        )
