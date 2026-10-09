from django.urls import path

from .views import MercadoPagoWebhookView, PixPaymentView

urlpatterns = [
    path("orders/<int:order_id>/pix/", PixPaymentView.as_view()),
    path("webhooks/mercado-pago/", MercadoPagoWebhookView.as_view()),
]
