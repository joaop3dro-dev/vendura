from django.contrib import admin
from django.urls import include, path

api_patterns = [
    path("users/", include("apps.users.urls")),
    path("", include("apps.products.urls")),  # products app urls
    path("", include("apps.stores.urls")),  # stores app urls
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_patterns)),
]
