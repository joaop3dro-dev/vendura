from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import FinalizeOrderSerializer, OrderSerializer
from .services import finalize_order


class FinalizeOrderView(APIView):
    def post(self, request):
        serializer = FinalizeOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = finalize_order(
            customer=request.user,
            itens=serializer.validated_data["itens"],
            cupom_code=serializer.validated_data.get("cupom_code"),
        )

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
