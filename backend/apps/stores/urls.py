from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import StoreSellerViewSet, StoreStaffViewSet

staff_store_router = SimpleRouter()
staff_store_router.register("store", StoreStaffViewSet, basename="staff-store")

seller_store_router = SimpleRouter()
seller_store_router.register("store", StoreSellerViewSet, basename="seller-store")

urlpatterns = [
    path("me/", include(seller_store_router.urls)),
    path("staff/", include(staff_store_router.urls)),
]
