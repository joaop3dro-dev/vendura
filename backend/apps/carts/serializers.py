from rest_framework import serializers

from apps.products.models import Product
from apps.products.serializers import ProductSerializer

from .models import Cart, CartItem


class CreateCartItemSerializer(serializers.ModelSerializer):
    item = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(public=True)
    )

    class Meta:
        model = CartItem
        fields = ["id", "item", "quantity"]
        read_only_fields = ["id"]


class CartItemSerializer(serializers.ModelSerializer):
    item = ProductSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "item", "quantity", "selected"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "items"]


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["quantity", "selected"]
