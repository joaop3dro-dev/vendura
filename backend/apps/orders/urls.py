from django.urls import path

from .views import (
    CancelOrderView,
    FinalizeDirectProductView,
    FinalizeOrderCartView,
    OrderView,
)

urlpatterns = [
    path("finalize-cart/", FinalizeOrderCartView.as_view()),
    path("finalize-direct/", FinalizeDirectProductView.as_view()),
    path("", OrderView.as_view()),
    path("<int:pk>/cancel/", CancelOrderView.as_view()),
]
