from django.urls import path

from .views import CartView, CreateCartItemView, DeleteCartItemView

urlpatterns = [
    path("item/", CreateCartItemView.as_view()),
    path("item/<int:pk>", DeleteCartItemView.as_view()),
    path("", CartView.as_view()),
]
