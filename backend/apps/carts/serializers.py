from rest_framework import serializers

from apps.products.serializers import ProductSerializer

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    item = ProductSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "item", "quantity", "selected"]


class CartSerializer(serializers.ModelSerializer):
    itens = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "itens"]
