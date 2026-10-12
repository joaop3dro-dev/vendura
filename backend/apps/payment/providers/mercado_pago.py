from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

import requests
from django.conf import settings

from ..exceptions import (
    MercadoPagoConfigurationError,
    MercadoPagoInvalidResponseError,
    MercadoPagoRequestError,
    MercadoPagoUnavailableError,
)


@dataclass(frozen=True)
class MercadoPagoPixData:
    order_id: str
    payment_id: str
    status: str
    status_detail: str
    pix_copy_paste: str
    ticket_url: str


@dataclass(frozen=True)
class MercadoPagoCancellationData:
    status: str
    status_detail: str


@dataclass(frozen=True)
class MercadoPagoGetOrderData:
    order_id: str
    payment_id: str
    total_amount: Decimal
    external_reference: UUID
    payment_method_id: str
    status: str
    status_detail: str
    paid_amount: Decimal


class MercadoPagoClient:
    def __init__(self, access_token=None, base_url=None, timeout_seconds=None):
        self.access_token = access_token or settings.MERCADO_PAGO_ACCESS_TOKEN
        self.base_url = base_url or settings.MERCADO_PAGO_API_BASE_URL
        self.timeout_seconds = timeout_seconds or settings.MERCADO_PAGO_TIMEOUT_SECONDS

        if not self.access_token:
            raise MercadoPagoConfigurationError(
                "MERCADO_PAGO_ACCESS_TOKEN não configurado"
            )
        if not self.base_url:
            raise MercadoPagoConfigurationError("MERCADO_PAGO_BASE_URL não configurado")
        if not self.timeout_seconds:
            raise MercadoPagoConfigurationError(
                "MERCADO_PAGO_TIMEOUT_SECONDS não configurado"
            )

    def create_pix(self, payment, payer_email) -> MercadoPagoPixData:
        amount = f"{payment.amount:.2f}"

        payload = {
            "type": "online",
            "total_amount": amount,
            "external_reference": str(payment.external_reference),
            "processing_mode": "automatic",
            "transactions": {
                "payments": [
                    {
                        "amount": amount,
                        "payment_method": {"id": "pix", "type": "bank_transfer"},
                        "expiration_time": (
                            f"PT{settings.MERCADO_PAGO_PIX_EXPIRATION_MINUTES}M"
                        ),
                    }
                ]
            },
            "payer": {
                "email": payer_email,
            },
        }

        try:
            response = requests.post(
                f"{self.base_url}/v1/orders",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "X-Idempotency-Key": str(payment.idempotency_key),
                },
                json=payload,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise MercadoPagoUnavailableError(
                "Erro ao se conectar com a API do Mercado Pago"
            ) from exc

        try:
            if response.status_code == 429 or response.status_code >= 500:
                raise MercadoPagoUnavailableError(
                    f"Mercado Pago respondeu HTTP {response.status_code}"
                )
            response.raise_for_status()

        except requests.HTTPError as exc:
            raise MercadoPagoRequestError(
                f"Mercado Pago respondeu HTTP {response.status_code}"
            ) from exc

        try:
            data = response.json()
            provider_payment = data["transactions"]["payments"][0]
            payment_method = provider_payment["payment_method"]

            return MercadoPagoPixData(
                order_id=data["id"],
                payment_id=provider_payment["id"],
                status=provider_payment["status"],
                status_detail=provider_payment["status_detail"],
                pix_copy_paste=payment_method["qr_code"],
                ticket_url=payment_method["ticket_url"],
            )
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise MercadoPagoInvalidResponseError(
                "Resposta inválida da API do Mercado Pago"
            ) from exc

    def cancel_order_payment(self, provider_order_id, cancel_idempotency_key):
        try:
            response = requests.post(
                f"{self.base_url}/v1/orders/{provider_order_id}/cancel",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "X-Idempotency-Key": str(cancel_idempotency_key),
                },
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise MercadoPagoUnavailableError(
                "Erro ao cancelar o Pix no Mercado Pago"
            ) from exc

        if response.status_code == 429 or response.status_code >= 500:
            raise MercadoPagoUnavailableError(
                f"Mercado Pago respondeu HTTP {response.status_code}"
            )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise MercadoPagoRequestError(
                f"Mercado Pago respondeu HTTP {response.status_code}"
            ) from exc

        try:
            data = response.json()
            provider_payment = data["transactions"]["payments"][0]

            return MercadoPagoCancellationData(
                status=provider_payment["status"],
                status_detail=provider_payment["status_detail"],
            )
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise MercadoPagoInvalidResponseError(
                "Resposta inválida da API do Mercado Pago"
            ) from exc

    def get_provider_order(self, provider_order_id):
        try:
            response = requests.get(
                f"{self.base_url}/v1/orders/{provider_order_id}",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise MercadoPagoUnavailableError(
                "Erro ao coletar os dados da API do Mercado Pago"
            ) from exc

        if response.status_code == 429 or response.status_code >= 500:
            raise MercadoPagoUnavailableError(
                f"Mercado Pago respondeu HTTP {response.status_code}"
            )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise MercadoPagoRequestError(
                f"Mercado Pago respondeu HTTP {response.status_code}"
            ) from exc

        try:
            data = response.json()
            provider_payment = data["transactions"]["payments"][0]

            return MercadoPagoGetOrderData(
                order_id=data["id"],
                payment_id=provider_payment["id"],
                total_amount=Decimal(data["total_amount"]),
                external_reference=UUID(data["external_reference"]),
                payment_method_id=provider_payment["payment_method"]["id"],
                status=provider_payment["status"],
                status_detail=provider_payment["status_detail"],
                paid_amount=Decimal(provider_payment["paid_amount"]),
            )
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise MercadoPagoInvalidResponseError(
                "Resposta inválida da API do Mercado Pago"
            ) from exc
