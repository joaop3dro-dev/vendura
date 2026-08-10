from rest_framework import serializers

from apps.products.models import Product

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "quantity", "unit_price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "total",
            "status",
            "status_display",
            "created_at",
            "delivery_address",
            "items",
        ]
        read_only_fields = ["delivery_address"]


class OrderItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(public=True)
    )
    quantity = serializers.IntegerField(min_value=1)


class CreateOrderCartSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(min_value=1)
    coupon_code = serializers.CharField(required=False, allow_null=True)


class CreateOrderDirectSerializer(serializers.Serializer):
    item = OrderItemInputSerializer()
    address_id = serializers.IntegerField(min_value=1)
    coupon_code = serializers.CharField(required=False, allow_null=True)
