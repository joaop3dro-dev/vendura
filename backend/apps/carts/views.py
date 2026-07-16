from django.db.models import Prefetch
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView

from .models import Cart, CartItem
from .serializers import CartItemSerializer, CartSerializer


class CreateCartItemView(CreateAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(customer=self.request.user)
        serializer.save(cart=cart)


class DeleteCartItemView(DestroyAPIView):
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
