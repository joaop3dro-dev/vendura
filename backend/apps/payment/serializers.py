from rest_framework import serializers

from .models import Payment


class PixPaymentSerializer(serializers.ModelSerializer):
    expires_at = serializers.DateTimeField(source="order.expires_at", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "status",
            "amount",
            "pix_copy_paste",
            "ticket_url",
            "expires_at",
            "created_at",
        ]
