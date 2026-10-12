from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

spectacular_patterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema")),
]

api_patterns = [
    path("users/", include("apps.users.urls")),
    path("", include("apps.products.urls")),  # products app urls
    path("orders/", include("apps.orders.urls")),
    path("", include(spectacular_patterns)),
    path("cart/", include("apps.carts.urls")),
    path("customers/", include("apps.customers.urls")),
    path("payment/", include("apps.payment.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_patterns)),
]
