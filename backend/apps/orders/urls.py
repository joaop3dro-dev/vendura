from django.urls import path

from .views import (
    CancelOrderView,
    CreateOrderCartView,
    CreateOrderDirectView,
    OrderView,
)

urlpatterns = [
    path("finalize-cart/", CreateOrderCartView.as_view()),
    path("finalize-direct/", CreateOrderDirectView.as_view()),
    path("", OrderView.as_view()),
    path("<int:pk>/cancel/", CancelOrderView.as_view()),
]
