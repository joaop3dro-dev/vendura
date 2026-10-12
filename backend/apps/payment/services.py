from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.orders.exceptions import OrderError
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
from .providers.mercado_pago import MercadoPagoClient, MercadoPagoGetOrderData
from .repositories import PaymentRepository


class PaymentService:
    @staticmethod
    @transaction.atomic
    def get_or_create_pix_payment(customer, order_id):
        order = OrderRepository.get_order_for_update(customer, order_id)

        now = timezone.now()

        if order.status != Order.Status.PENDING:
            raise PaymentOrderNotAvailableError(
                f"Pedido com status '{order.status}' não está disponível para pagamento"
            )

        if order.expires_at <= now:
            raise PaymentOrderNotAvailableError(
                "Pedido expirado e indisponível para pagamento"
            )

        payment = PaymentRepository.get_active_by_order(order)
        if payment:
            return payment, False

        pix_duration = timedelta(
            minutes=settings.MERCADO_PAGO_PIX_EXPIRATION_MINUTES,
            seconds=settings.MERCADO_PAGO_PIX_EXPIRATION_SAFETY_MARGIN_SECONDS,
        )

        if order.expires_at <= now + pix_duration:
            raise PaymentOrderNotAvailableError(
                "O prazo restante do pedido é insuficiente para gerar um Pix"
            )

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
    def process_order_notification(provider_order_id):
        order_data = MercadoPagoClient().get_provider_order(provider_order_id)

        if order_data.status != "processed" or order_data.status_detail != "accredited":
            return None

        return PaymentService.confirm_pix_payment(order_data)

    @staticmethod
    @transaction.atomic
    def confirm_pix_payment(order_data: MercadoPagoGetOrderData):
        order = OrderRepository.get_order_for_update_by_kwargs(
            payments__mercado_pago_payment_id=order_data.payment_id
        )
        payment = PaymentRepository.get_by_provider_payment_id(order_data.payment_id)

        is_alredy_paid = PaymentService._validate_payment_and_order(
            payment, order, order_data
        )
        if is_alredy_paid:
            return payment, order

        payment.status = Payment.Status.APPROVED
        payment.provider_status = order_data.status
        payment.provider_status_detail = order_data.status_detail
        payment.approved_at = timezone.now()
        payment.last_error = ""

        payment.save(
            update_fields=[
                "status",
                "provider_status",
                "provider_status_detail",
                "approved_at",
                "last_error",
                "updated_at",
            ]
        )

        order.approve()

        return payment, order

    @staticmethod
    def _validate_payment_and_order(
        payment: Payment, order: Order, order_data: MercadoPagoGetOrderData
    ):
        if payment.mercado_pago_order_id != order_data.order_id:
            raise PaymentError(
                "provider_order_id é incompatível com o mercado_pago_order_id do pagamento"
            )

        if (
            payment.status == Payment.Status.APPROVED
            and order.status == Order.Status.PAID
        ):
            return True

        if payment.status != Payment.Status.PENDING:
            raise PaymentError("Este pagamento não pode ser aprovado")

        if order_data.status != "processed" or order_data.status_detail != "accredited":
            raise PaymentError(
                "Os status do provedor atuais não permitem a aprovação do pagamento"
            )

        if order.total != order_data.total_amount:
            raise OrderError("O total do serviço não corresponde ao total local")

        if payment.amount != order_data.paid_amount:
            raise PaymentError("O total pago não correspondeu ao valor registrado")

        if payment.external_reference != order_data.external_reference:
            raise PaymentError("'external_reference' não corresponde")

        if order_data.payment_method_id != "pix":
            raise PaymentError("O método informado não corresponde")

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

    @staticmethod
    @transaction.atomic
    def expire_order(order_id):
        order = OrderRepository.get_order_for_update_by_id(order_id)
        payment = PaymentRepository.get_active_for_update_by_order(order)

        expired_order = OrderService.expire_locked_order(order)

        if expired_order is None:
            return None

        if payment is not None:
            payment.status = Payment.Status.EXPIRED
            payment.save(update_fields=["status", "updated_at"])

        return expired_order
