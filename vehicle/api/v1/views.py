from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from vehicle.models import (
    DriverNotification,
    ManagerNotification,
    MechanicNotification,
    Request,
)
from .serializers import (
    MobileLogoutSerializer,
    MobileTokenObtainPairSerializer,
    MobileTokenResponseSerializer,
    MobileUserSerializer,
    NotificationReadSerializer,
    RequestReadSerializer,
    get_mobile_profile,
)

@extend_schema_view(
    post=extend_schema(responses=MobileTokenResponseSerializer),
)
class MobileLoginView(TokenObtainPairView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth_login"
    serializer_class = MobileTokenObtainPairSerializer


class MobileTokenRefreshView(TokenRefreshView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth_refresh"


class MobileLogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(request=MobileLogoutSerializer, responses={204: None})
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not isinstance(refresh_token, str) or not refresh_token:
            return Response(
                {"detail": "A refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            if str(token.get("user_id")) != str(request.user.pk):
                return Response(
                    {"detail": "The refresh token does not belong to this account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "The refresh token is invalid or expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class MobileProfileView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=MobileUserSerializer)
    def get(self, request):
        return Response(MobileUserSerializer(request.user).data)


@method_decorator(never_cache, name="dispatch")
class MobileNotificationListView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NotificationReadSerializer

    def get_queryset(self):
        role, profile = get_mobile_profile(self.request.user)
        if role == "driver":
            notifications = DriverNotification.objects.filter(driver=profile)
        elif role == "mechanic":
            notifications = MechanicNotification.objects.filter(mechanic=profile)
        else:
            notifications = ManagerNotification.objects.filter(manager=profile)
        return notifications.order_by("-timestamp", "-pk")


class MobileRequestScopeMixin:
    serializer_class = RequestReadSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        role, profile = get_mobile_profile(self.request.user)
        if not profile.is_email_verified:
            raise PermissionDenied("Verify your email to access service requests.")
        if role != "driver" and not profile.status:
            raise PermissionDenied("This profile is awaiting approval.")

        requests = Request.objects.select_related(
            "driver__user", "mechanic__user", "manager__user"
        ).order_by("-date", "-pk")

        if role == "driver":
            return requests.filter(driver=profile)
        if role == "mechanic":
            return requests.filter(mechanic=profile)
        return requests.filter(manager=profile)


class MobileRequestListView(MobileRequestScopeMixin, generics.ListAPIView):
    pass


class MobileRequestDetailView(MobileRequestScopeMixin, generics.RetrieveAPIView):
    lookup_field = "pk"
