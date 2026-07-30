from django.db.models import Prefetch
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.response import Response

from .models import Cart, CartItem
from .serializers import (
    CartItemSerializer,
    CartSerializer,
    CreateCartItemSerializer,
    UpdateCartItemSerializer,
)


class CreateCartItemView(CreateAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CreateCartItemSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart, _ = Cart.objects.get_or_create(customer=self.request.user)
        item = serializer.validated_data["item"]
        quantity = serializer.validated_data["quantity"]

        cart_item = CartItem.objects.filter(cart=cart, item=item).first()

        if cart_item:
            cart_item.quantity += quantity
            cart_item.save(update_fields=["quantity"])

            return Response(
                CartItemSerializer(cart_item).data, status=status.HTTP_200_OK
            )

        cart_item = serializer.save(cart=cart)

        return Response(
            CartItemSerializer(cart_item).data, status=status.HTTP_201_CREATED
        )


class UpdateDestroyCartItemView(RetrieveUpdateDestroyAPIView):
    serializer_class = UpdateCartItemSerializer
    queryset = CartItem.objects.all()

    def get_queryset(self):
        return CartItem.objects.filter(cart__customer=self.request.user)


class CartView(ListAPIView):
    queryset = Cart.objects.all()
    pagination_class = None
    serializer_class = CartSerializer

    def get_queryset(self):
        return Cart.objects.filter(customer=self.request.user).prefetch_related(
            Prefetch("itens", queryset=CartItem.objects.select_related("item"))
        )
