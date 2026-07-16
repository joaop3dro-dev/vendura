from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (
    CategoryPublicViewSet,
    CategoryViewSet,
    ProductPublicViewSet,
    ProductStaffViewSet,
)

staff_product_router = SimpleRouter()
staff_product_router.register(
    "products", ProductStaffViewSet, basename="staff-products"
)


public_product_router = SimpleRouter()
public_product_router.register("", ProductPublicViewSet, basename="public-products")

public_category_router = SimpleRouter()
public_category_router.register("", CategoryPublicViewSet, basename="public-category")

staff_category_router = SimpleRouter()
staff_category_router.register("category", CategoryViewSet, basename="staff-category")

staff_urls = staff_product_router.urls + staff_category_router.urls

urlpatterns = [
    path("category/", include(staff_category_router.urls)),
    path("products/", include(public_product_router.urls)),
    path("staff/", include(staff_urls)),
]
