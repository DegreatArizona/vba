from django.urls import path
from drf_spectacular.views import SpectacularAPIView

from .views import (
    MobileLoginView,
    MobileLogoutView,
    MobileManagerMechanicListView,
    MobileManagerRequestClaimView,
    MobileManagerRequestQueueView,
    MobileMechanicRequestActionView,
    MobileNotificationListView,
    MobileNotificationMarkAllReadView,
    MobileDeviceTokenRegistrationView,
    MobileNotificationReadView,
    MobileProfileView,
    MobileRegistrationView,
    MobileResendVerificationView,
    MobileRequestDetailView,
    MobileRequestListView,
    MobileTokenRefreshView,
)

app_name = "mobile_api_v1"

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("auth/login/", MobileLoginView.as_view(), name="login"),
    path("auth/register/", MobileRegistrationView.as_view(), name="register"),
    path("auth/resend-verification/", MobileResendVerificationView.as_view(), name="resend-verification"),
    path("auth/refresh/", MobileTokenRefreshView.as_view(), name="refresh"),
    path("auth/logout/", MobileLogoutView.as_view(), name="logout"),
    path("push-tokens/register/", MobileDeviceTokenRegistrationView.as_view(), name="push-token-register"),
    path("me/", MobileProfileView.as_view(), name="me"),
    path("manager/mechanics/", MobileManagerMechanicListView.as_view(), name="manager-mechanics"),
    path("manager/queue/", MobileManagerRequestQueueView.as_view(), name="manager-request-queue"),
    path(
        "manager/queue/<int:request_id>/claim/",
        MobileManagerRequestClaimView.as_view(),
        name="manager-request-claim",
    ),
    path("requests/", MobileRequestListView.as_view(), name="requests"),
    path("requests/<int:pk>/", MobileRequestDetailView.as_view(), name="request-detail"),
    path(
        "requests/<int:request_id>/actions/",
        MobileMechanicRequestActionView.as_view(),
        name="request-actions",
    ),
    path("notifications/read-all/", MobileNotificationMarkAllReadView.as_view(), name="notifications-read-all"),
    path(
        "notifications/<int:notification_id>/read/",
        MobileNotificationReadView.as_view(),
        name="notification-read",
    ),
    path("notifications/", MobileNotificationListView.as_view(), name="notifications"),
]
