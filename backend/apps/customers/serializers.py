from rest_framework import serializers

from .models import Address


class AddressSerializer(serializers.ModelSerializer):
    full_address = serializers.CharField(read_only=True)

    class Meta:
        model = Address
        fields = (
            "id",
            "street",
            "number",
            "neighborhood",
            "city",
            "state",
            "zip_code",
            "full_address",
        )
