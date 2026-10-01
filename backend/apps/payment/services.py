from uuid import uuid4

from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order
from apps.orders.repositories import OrderRepository
from apps.orders.services import OrderService

from .exceptions import (
    MercadoPagoInvalidResponseError,
    MercadoPagoRequestError,
    MercadoPagoUnavailableError,
    PaymentCancellationPendingError,
    PaymentError,
    PaymentOrderNotAvailableError,
)
from .models import Payment
from .providers.mercado_pago import MercadoPagoClient
from .repositories import PaymentRepository


class PaymentService:
    @staticmethod
    @transaction.atomic
    def get_or_create_pix_payment(customer, order_id):
        order = OrderRepository.get_order_for_update(customer, order_id)

        if order.status != Order.Status.PENDING:
            raise PaymentOrderNotAvailableError(
                f"Pedido com status '{order.status}' não está disponível para pagamento"
            )

        if order.expires_at <= timezone.now():
            raise PaymentOrderNotAvailableError(
                "Pedido expirado e indisponível para pagamento"
            )

        payment = PaymentRepository.get_active_by_order(order)
        if payment:
            return payment, False

        payment = PaymentRepository.create_payment(order)

        return payment, True

    @staticmethod
    def generate_pix(customer, order_id):
        payment, _ = PaymentService.get_or_create_pix_payment(customer, order_id)

        if payment.status == Payment.Status.PENDING:
            return payment

        try:
            pix_data = MercadoPagoClient().create_pix(
                payment=payment, payer_email=customer.user.email
            )
        except (MercadoPagoUnavailableError, MercadoPagoInvalidResponseError) as exc:
            PaymentService._record_retryable_error(payment.id, str(exc))
            raise
        except MercadoPagoRequestError as exc:
            PaymentService._mark_provider_error(payment.id, str(exc))
            raise

        return PaymentService._mark_pending(payment.id, pix_data)

    @staticmethod
    def cancel_order(customer, order_id):
        order, cancellation = PaymentService._prepare_order_cancellation(
            customer, order_id
        )

        if cancellation is None:
            return order

        payment_id, provider_order_id, cancel_key = cancellation

        try:
            cancellation_data = MercadoPagoClient().cancel_order_payment(
                provider_order_id, cancel_key
            )
        except (
            MercadoPagoInvalidResponseError,
            MercadoPagoUnavailableError,
            MercadoPagoRequestError,
        ) as exc:
            PaymentService._record_cancellation_error(payment_id, str(exc))
            raise

        return PaymentService._complete_order_cancellation(
            customer, order_id, payment_id, cancellation_data
        )

    @staticmethod
    @transaction.atomic
    def _complete_order_cancellation(customer, order_id, payment_id, cancellation_data):
        order = OrderRepository.get_order_for_update(customer, order_id)
        payment = PaymentRepository.get_for_update(payment_id)

        payment.status = Payment.Status.CANCELED
        payment.provider_status = cancellation_data.status
        payment.provider_status_detail = cancellation_data.status_detail
        payment.save(
            update_fields=[
                "status",
                "provider_status",
                "provider_status_detail",
                "updated_at",
            ]
        )

        return OrderService.cancel_locked_order(order)

    @staticmethod
    @transaction.atomic
    def _prepare_order_cancellation(customer, order_id):
        order = OrderRepository.get_order_for_update(customer, order_id)
        payment = PaymentRepository.get_active_for_update_by_order(order)

        if payment is None:
            return OrderService.cancel_locked_order(order), None

        if payment.status == Payment.Status.CREATED:
            raise PaymentCancellationPendingError(
                "A criação do Pix ainda precisa ser confirmada"
            )

        if payment.cancel_idempotency_key is None:
            payment.cancel_idempotency_key = uuid4()
            payment.save(update_fields=["cancel_idempotency_key", "updated_at"])

        return order, (
            payment.id,
            payment.mercado_pago_order_id,
            payment.cancel_idempotency_key,
        )

    @staticmethod
    @transaction.atomic
    def _record_cancellation_error(payment_id, exc):
        payment = PaymentRepository.get_for_update(payment_id)

        if payment.status == Payment.Status.PENDING:
            payment.last_error = exc
            payment.save(update_fields=["last_error", "updated_at"])

    @staticmethod
    @transaction.atomic
    def _record_retryable_error(payment_id, exc):
        payment = PaymentRepository.get_for_update(payment_id)

        if payment.status == Payment.Status.CREATED:
            payment.last_error = exc
            payment.save(update_fields=["last_error", "updated_at"])

        return payment

    @staticmethod
    @transaction.atomic
    def _mark_provider_error(payment_id, exc):
        payment = PaymentRepository.get_for_update(payment_id)

        if payment.status == Payment.Status.CREATED:
            payment.status = Payment.Status.ERROR
            payment.last_error = exc
            payment.save(update_fields=["status", "last_error", "updated_at"])

        return payment

    @staticmethod
    @transaction.atomic
    def _mark_pending(payment_id, pix_data):
        payment = PaymentRepository.get_for_update(payment_id)

        if payment.status == Payment.Status.PENDING:
            return payment

        if payment.status != Payment.Status.CREATED:
            raise PaymentError(
                f"Pagamento com status '{payment.status}' não pode receber um PIX"
            )

        payment.status = Payment.Status.PENDING
        payment.mercado_pago_order_id = pix_data.order_id
        payment.mercado_pago_payment_id = pix_data.payment_id
        payment.provider_status = pix_data.status
        payment.provider_status_detail = pix_data.status_detail
        payment.pix_copy_paste = pix_data.pix_copy_paste
        payment.ticket_url = pix_data.ticket_url
        payment.last_error = ""

        payment.save(
            update_fields=[
                "status",
                "mercado_pago_order_id",
                "mercado_pago_payment_id",
                "provider_status",
                "provider_status_detail",
                "pix_copy_paste",
                "ticket_url",
                "last_error",
                "updated_at",
            ]
        )

        return payment
