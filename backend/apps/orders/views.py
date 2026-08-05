from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.customers.repositories import CustomerRepository
from config.pagination import OrderPageNumberPagination

from .models import Order, OrderItem
from .serializers import (
    FinalizeOrderCartSerializer,
    FinalizeOrderOneProductSerializer,
    OrderSerializer,
)
from .services import cancel_order, finalize_direct_order, finalize_order_cart


class FinalizeOrderCartView(APIView):
    @extend_schema(
        request=FinalizeOrderCartSerializer, responses={201: OrderSerializer}
    )
    def post(self, request):
        serializer = FinalizeOrderCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = CustomerRepository.get_customer_by_user(request.user)

        order_id = finalize_order_cart(
            customer=customer,
            coupon_code=serializer.validated_data.get("coupon_code"),
            address_id=serializer.validated_data["address_id"],
        )

        order = Order.objects.prefetch_related(
            Prefetch("items", queryset=OrderItem.objects.select_related("product"))
        ).get(pk=order_id)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class FinalizeDirectProductView(APIView):
    @extend_schema(
        request=FinalizeOrderOneProductSerializer, responses={201: OrderSerializer}
    )
    def post(self, request):
        serializer = FinalizeOrderOneProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = CustomerRepository.get_customer_by_user(request.user)

        order_id = finalize_direct_order(
            customer=customer,
            coupon_code=serializer.validated_data.get("coupon_code"),
            item=serializer.validated_data["item"],
            address_id=serializer.validated_data["address_id"],
        )

        order = Order.objects.prefetch_related(
            Prefetch("items", queryset=OrderItem.objects.select_related("product"))
        ).get(pk=order_id)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderView(ListAPIView):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    pagination_class = OrderPageNumberPagination

    def get_queryset(self):
        customer = CustomerRepository.get_customer_by_user(self.request.user)
        return (
            Order.objects.prefetch_related(
                Prefetch("items", queryset=OrderItem.objects.select_related("product"))
            )
            .filter(customer=customer)
            .order_by("-created_at")
        )


class CancelOrderView(APIView):
    def post(self, request, pk):
        customer = CustomerRepository.get_customer_by_user(request.user)
        order = cancel_order(customer=customer, order_id=pk)

        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
