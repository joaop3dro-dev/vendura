from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import ProductPublicViewSet, ProductSellerViewSet, ProductStaffViewSet

staff_router = SimpleRouter()
staff_router.register("products", ProductStaffViewSet, basename="staff-products")

product_user_router = SimpleRouter()
product_user_router.register("products", ProductSellerViewSet, basename="user-products")

public_router = SimpleRouter()
public_router.register("", ProductPublicViewSet, basename="public-products")

urlpatterns = [
    path("products/", include(public_router.urls)),
    path("me/", include(product_user_router.urls)),
    path("staff/", include(staff_router.urls)),
]
