from django.urls import include, path

from ..customer.views.auth_views import (
    CookieTokenBlacklistView,
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
)
from ..customer.views.user_views import RegisterView

auth_patterns = [
    path("login/", CookieTokenObtainPairView.as_view()),
    path("refresh/", CookieTokenRefreshView.as_view()),
    path("logout/", CookieTokenBlacklistView.as_view()),
    path("register/", RegisterView.as_view()),
]

urlpatterns = [path("auth/", include(auth_patterns))]
