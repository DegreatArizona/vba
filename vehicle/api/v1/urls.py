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
    MobileProfileView,
    MobileRequestDetailView,
    MobileRequestListView,
    MobileTokenRefreshView,
)

app_name = "mobile_api_v1"

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("auth/login/", MobileLoginView.as_view(), name="login"),
    path("auth/refresh/", MobileTokenRefreshView.as_view(), name="refresh"),
    path("auth/logout/", MobileLogoutView.as_view(), name="logout"),
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
    path("notifications/", MobileNotificationListView.as_view(), name="notifications"),
]
