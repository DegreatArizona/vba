from django.urls import path

from .views import (
    MobileLoginView,
    MobileLogoutView,
    MobileProfileView,
    MobileRequestListView,
    MobileTokenRefreshView,
)

app_name = "mobile_api_v1"

urlpatterns = [
    path("auth/login/", MobileLoginView.as_view(), name="login"),
    path("auth/refresh/", MobileTokenRefreshView.as_view(), name="refresh"),
    path("auth/logout/", MobileLogoutView.as_view(), name="logout"),
    path("me/", MobileProfileView.as_view(), name="me"),
    path("requests/", MobileRequestListView.as_view(), name="requests"),
]
