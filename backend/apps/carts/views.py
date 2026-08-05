from django.db.models import Prefetch
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.response import Response

from apps.customers.repositories import CustomerRepository

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

        customer = CustomerRepository.get_customer_by_user(self.request.user)
        cart, _ = Cart.objects.get_or_create(customer=customer)
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
        customer = CustomerRepository.get_customer_by_user(self.request.user)
        return CartItem.objects.filter(cart__customer=customer)


class CartView(ListAPIView):
    queryset = Cart.objects.all()
    pagination_class = None
    serializer_class = CartSerializer

    def get_queryset(self):
        customer = CustomerRepository.get_customer_by_user(self.request.user)
        return Cart.objects.filter(customer=customer).prefetch_related(
            Prefetch("items", queryset=CartItem.objects.select_related("item"))
        )
