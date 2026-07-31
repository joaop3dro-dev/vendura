from django.urls import path

from .views import ListCreateAddressView, UpdateDestroyAddressView

urlpatterns = [
    path("addresses/", ListCreateAddressView.as_view()),
    path("addresses/<int:pk>/", UpdateDestroyAddressView.as_view()),
]
