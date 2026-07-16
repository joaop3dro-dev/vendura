from django.db.models import Prefetch
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, OrderItem
from .serializers import FinalizeOrderSerializer, OrderSerializer
from .services import finalize_order


class FinalizeOrderCartView(APIView):
    def post(self, request):
        serializer = FinalizeOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        itens_transform = [
            {"product": item["product"].id, "quantity": item["quantity"]}
            for item in serializer.validated_data["itens"]
        ]

        order_id = finalize_order(
            customer=request.user,
            itens=itens_transform,
            cupom_code=serializer.validated_data.get("cupom_code"),
        )

        order = Order.objects.prefetch_related(
            Prefetch("items", queryset=OrderItem.objects.select_related("product"))
        ).get(pk=order_id)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
