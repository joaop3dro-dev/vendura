from django.urls import path

from .views import CartView, CreateCartItemView, UpdateDestroyCartItemView

urlpatterns = [
    path("item/", CreateCartItemView.as_view()),
    path("item/<int:pk>", UpdateDestroyCartItemView.as_view()),
    path("", CartView.as_view()),
]
