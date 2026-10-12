from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.customers.repositories import CustomerRepository
from apps.orders.repositories import OrderRepository

from .repositories import PaymentRepository
from .serializers import PixPaymentSerializer
from .services import PaymentService


class PixPaymentView(APIView):
    @extend_schema(responses={200: PixPaymentSerializer})
    def post(self, request, order_id):
        customer = CustomerRepository.get_customer_by_user(request.user)

        payment = PaymentService.generate_pix(customer=customer, order_id=order_id)

        return Response(PixPaymentSerializer(payment).data, status=status.HTTP_200_OK)

    @extend_schema(responses={200: PixPaymentSerializer})
    def get(self, request, order_id):
        customer = CustomerRepository.get_customer_by_user(request.user)
        order = OrderRepository.get_order(customer, order_id)
        payment = PaymentRepository.get_latest_by_order_or_raise(order)

        return Response(PixPaymentSerializer(payment).data)


class MercadoPagoWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(exclude=True)
    def post(self, request):
        if request.data.get("type") != "order":
            return Response(status=status.HTTP_200_OK)

        try:
            provider_order_id = request.data["data"]["id"]
        except (KeyError, TypeError):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        PaymentService.process_order_notification(provider_order_id)

        return Response(status=status.HTTP_200_OK)
