import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from vehicle.request_services import (
    ManagerClaimConflict,
    MechanicActionConflict,
    RequestCreationConflict,
    claim_and_assign_request,
    create_driver_request,
    perform_mechanic_request_action,
)
from vehicle.models import (
    Driver,
    DriverNotification,
    ManagerNotification,
    Mechanic,
    MechanicNotification,
    MobileDeviceToken,
    Request,
)
from vehicle.utils import generate_token, send_html_email
from .serializers import (
    ManagerMechanicPageSerializer,
    ManagerMechanicSummarySerializer,
    ManagerQueueRequestSerializer,
    ManagerRequestClaimSerializer,
    MechanicRequestActionSerializer,
    MobileDeviceTokenRegistrationSerializer,
    MobileDeviceTokenResponseSerializer,
    MobileLogoutSerializer,
    MobileRegistrationResponseSerializer,
    MobileRegistrationSerializer,
    MobileResendVerificationResponseSerializer,
    MobileResendVerificationSerializer,
    MobileTokenObtainPairSerializer,
    MobileTokenResponseSerializer,
    MobileUserSerializer,
    NotificationMarkAllReadResponseSerializer,
    NotificationReadSerializer,
    RequestCreateSerializer,
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


User = get_user_model()
logger = logging.getLogger(__name__)


def send_mobile_verification_email(user):
    token = generate_token(user.email)
    verification_link = f"{settings.SITE_URL}/verify-email/{token}"
    send_html_email(
        subject="Verify your Auto Aid account",
        template_name="mails/verify.html",
        context={
            "user": user,
            "message1": "Verify Your Email",
            "message2": "Click the link below to verify your email:",
            "link": verification_link,
        },
        recipient_list=[user.email],
    )


class MobileRegistrationView(APIView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth_register"

    @extend_schema(
        request=MobileRegistrationSerializer,
        responses={201: MobileRegistrationResponseSerializer},
        tags=["Auth"],
    )
    def post(self, request):
        serializer = MobileRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data["role"]
        try:
            user = serializer.save()
        except IntegrityError:
            return Response(
                {"detail": "This username or email is already in use."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            send_mobile_verification_email(user)
        except Exception:
            logger.exception("Mobile account verification email could not be sent.")

        return Response(
            {
                "detail": "Account created. Verify your email before using service features. If the email does not arrive, request another link.",
                "role": role,
                "verification_required": True,
            },
            status=status.HTTP_201_CREATED,
        )


class MobileResendVerificationView(APIView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth_resend"

    @extend_schema(
        request=MobileResendVerificationSerializer,
        responses={202: MobileResendVerificationResponseSerializer},
        tags=["Auth"],
    )
    def post(self, request):
        serializer = MobileResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email__iexact=serializer.validated_data["email"]).first()
        if user:
            driver = Driver.objects.filter(user=user).first()
            mechanic = Mechanic.objects.filter(user=user).first()
            profiles = [profile for profile in (driver, mechanic) if profile is not None]
            if len(profiles) == 1 and not profiles[0].is_email_verified:
                try:
                    send_mobile_verification_email(user)
                except Exception:
                    logger.exception("Mobile account verification email could not be resent.")

        return Response(
            {"detail": "If an unverified driver or mechanic account exists for that email, verification instructions will be sent."},
            status=status.HTTP_202_ACCEPTED,
        )


class MobileTokenRefreshView(TokenRefreshView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth_refresh"


class MobileLogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(request=MobileLogoutSerializer, responses={204: None})
    def post(self, request):
        serializer = MobileLogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data["refresh"]

        try:
            token = RefreshToken(refresh_token)
            if str(token.get("user_id")) != str(request.user.pk):
                return Response(
                    {"detail": "The refresh token does not belong to this account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            with transaction.atomic():
                token.blacklist()
                push_token = serializer.validated_data.get("push_token")
                if push_token:
                    MobileDeviceToken.objects.filter(
                        user=request.user,
                        expo_push_token=push_token,
                        is_active=True,
                    ).update(is_active=False, updated_at=timezone.now())
        except TokenError:
            return Response(
                {"detail": "The refresh token is invalid or expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class MobileDeviceTokenRegistrationView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "push_token_register"

    @extend_schema(
        request=MobileDeviceTokenRegistrationSerializer,
        responses={200: MobileDeviceTokenResponseSerializer},
        tags=["Push notifications"],
    )
    def post(self, request):
        get_mobile_profile(request.user)
        serializer = MobileDeviceTokenRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        previous_token = serializer.validated_data.get("previous_token")
        now = timezone.now()

        with transaction.atomic():
            if previous_token and previous_token != token:
                MobileDeviceToken.objects.filter(
                    user=request.user,
                    expo_push_token=previous_token,
                    is_active=True,
                ).update(is_active=False, updated_at=now)

            MobileDeviceToken.objects.update_or_create(
                expo_push_token=token,
                defaults={
                    "user": request.user,
                    "platform": serializer.validated_data["platform"],
                    "is_active": True,
                    "last_registered_at": now,
                },
            )

        return Response({"registered": True}, status=status.HTTP_200_OK)


class MobileProfileView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=MobileUserSerializer)
    def get(self, request):
        return Response(MobileUserSerializer(request.user).data)


def get_mobile_notification_queryset(user):
    role, profile = get_mobile_profile(user)
    if role == "driver":
        notifications = DriverNotification.objects.filter(driver=profile)
    elif role == "mechanic":
        notifications = MechanicNotification.objects.filter(mechanic=profile)
    else:
        notifications = ManagerNotification.objects.filter(manager=profile)
    return notifications.order_by("-timestamp", "-pk")


@method_decorator(never_cache, name="dispatch")
class MobileNotificationListView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NotificationReadSerializer

    def get_queryset(self):
        return get_mobile_notification_queryset(self.request.user)


@method_decorator(never_cache, name="dispatch")
class MobileNotificationReadView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NotificationReadSerializer

    @extend_schema(request=None, responses=NotificationReadSerializer, tags=["Notifications"])
    def post(self, request, notification_id):
        notification = get_mobile_notification_queryset(request.user).filter(pk=notification_id).first()
        if notification is None:
            raise NotFound("This notification is unavailable.")

        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])
        return Response(NotificationReadSerializer(notification).data, status=status.HTTP_200_OK)


@method_decorator(never_cache, name="dispatch")
class MobileNotificationMarkAllReadView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NotificationMarkAllReadResponseSerializer

    @extend_schema(
        request=None,
        responses=NotificationMarkAllReadResponseSerializer,
        tags=["Notifications"],
    )
    def post(self, request):
        updated_count = get_mobile_notification_queryset(request.user).filter(is_read=False).update(is_read=True)
        return Response({"updated_count": updated_count}, status=status.HTTP_200_OK)


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


@extend_schema_view(
    post=extend_schema(
        request=RequestCreateSerializer,
        responses={
            201: RequestReadSerializer,
            409: OpenApiResponse(description="An active request or unpaid invoice prevents another request."),
        },
        tags=["Requests"],
    ),
)
class MobileRequestListView(MobileRequestScopeMixin, generics.ListCreateAPIView):
    throttle_scope = "request_create"

    def get_serializer_class(self):
        if self.request.method == "POST":
            return RequestCreateSerializer
        return RequestReadSerializer

    def get_throttles(self):
        if self.request.method == "POST":
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def create(self, request, *args, **kwargs):
        role, profile = get_mobile_profile(request.user)
        if role != "driver":
            raise PermissionDenied("Only drivers can create roadside service requests.")
        if not profile.is_email_verified:
            raise PermissionDenied("Verify your email before creating a service request.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            service_request = create_driver_request(
                driver=profile,
                values=serializer.validated_data,
            )
        except RequestCreationConflict as conflict:
            return Response(
                {"detail": conflict.detail, "code": conflict.code},
                status=status.HTTP_409_CONFLICT,
            )

        response_data = RequestReadSerializer(service_request).data
        return Response(response_data, status=status.HTTP_201_CREATED)


class MobileRequestDetailView(MobileRequestScopeMixin, generics.RetrieveAPIView):
    lookup_field = "pk"


class MobileMechanicRequestActionView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "request_action"

    @extend_schema(
        request=MechanicRequestActionSerializer,
        responses={
            200: RequestReadSerializer,
            404: OpenApiResponse(description="The request is not assigned to this mechanic."),
            409: OpenApiResponse(description="The action is invalid for the current request state."),
        },
        tags=["Requests"],
    )
    def post(self, request, request_id):
        role, mechanic = get_mobile_profile(request.user)
        if role != "mechanic":
            raise PermissionDenied("Only mechanics can update assigned work.")
        if not mechanic.is_email_verified:
            raise PermissionDenied("Verify your email before updating assigned work.")
        if not mechanic.status:
            raise PermissionDenied("This mechanic profile is awaiting approval.")

        serializer = MechanicRequestActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            service_request = perform_mechanic_request_action(
                mechanic=mechanic,
                request_id=request_id,
                action=serializer.validated_data["action"],
            )
        except Request.DoesNotExist:
            raise NotFound("This request is not assigned to your mechanic profile.")
        except MechanicActionConflict as conflict:
            return Response(
                {"detail": conflict.detail, "code": conflict.code},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(RequestReadSerializer(service_request).data, status=status.HTTP_200_OK)


class ManagerMechanicPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


@method_decorator(never_cache, name="dispatch")
class MobileManagerMechanicListView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=ManagerMechanicPageSerializer, tags=["Manager"])
    def get(self, request):
        role, manager = get_mobile_profile(request.user)
        if role != "manager":
            raise PermissionDenied("Only managers can view their assigned mechanic team.")
        if not manager.is_email_verified:
            raise PermissionDenied("Verify your email before accessing manager tools.")
        if not manager.status:
            raise PermissionDenied("This manager profile is awaiting approval.")

        mechanics = Mechanic.objects.filter(my_manager=manager).select_related("user").order_by(
            "user__first_name", "user__last_name", "pk"
        )
        paginator = ManagerMechanicPagination()
        page = paginator.paginate_queryset(mechanics, request, view=self) or []
        mechanic_ids = [mechanic.pk for mechanic in page]
        counts_by_mechanic = {}
        busy_mechanic_ids = set()
        if mechanic_ids:
            counts_by_mechanic = {
                row["mechanic_id"]: row
                for row in Request.objects.filter(
                    manager=manager,
                    mechanic_id__in=mechanic_ids,
                )
                .values("mechanic_id")
                .annotate(
                    assigned_request_count=Count("pk"),
                    active_request_count=Count(
                        "pk",
                        filter=Q(status__in=("Accepted", "Repairing", "Done")),
                    ),
                )
            }
            busy_mechanic_ids = set(
                Request.objects.filter(
                    mechanic_id__in=mechanic_ids,
                    status__in=("Accepted", "Repairing", "Done"),
                ).values_list("mechanic_id", flat=True)
            )

        results = []
        for mechanic in page:
            counts = counts_by_mechanic.get(mechanic.pk, {})
            results.append(
                {
                    "id": mechanic.pk,
                    "full_name": mechanic.get_name.strip() or f"Mechanic #{mechanic.pk}",
                    "union_name": mechanic.union_name,
                    "state": mechanic.state,
                    "local_government": mechanic.local_government,
                    "is_approved": mechanic.status,
                    "can_be_assigned": (
                        mechanic.status and mechanic.is_email_verified and mechanic.pk not in busy_mechanic_ids
                    ),
                    "assigned_request_count": counts.get("assigned_request_count", 0),
                    "active_request_count": counts.get("active_request_count", 0),
                }
            )

        serialized = ManagerMechanicSummarySerializer(results, many=True)
        return paginator.get_paginated_response(serialized.data)


@method_decorator(never_cache, name="dispatch")
class MobileManagerRequestQueueView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ManagerQueueRequestSerializer
    pagination_class = ManagerMechanicPagination

    @extend_schema(tags=["Manager"])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        role, manager = get_mobile_profile(self.request.user)
        if role != "manager":
            raise PermissionDenied("Only managers can view the regional request queue.")
        if not manager.is_email_verified:
            raise PermissionDenied("Verify your email before accessing manager tools.")
        if not manager.status:
            raise PermissionDenied("This manager profile is awaiting approval.")

        manager_state = (manager.state or "").strip()
        if not manager_state:
            raise PermissionDenied("Add a state to your manager profile before using the request queue.")

        return Request.objects.filter(
            state__iexact=manager_state,
            status="Pending",
            manager__isnull=True,
            mechanic__isnull=True,
        ).order_by("-date", "-pk")


class MobileManagerRequestClaimView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "manager_claim"

    @extend_schema(
        request=ManagerRequestClaimSerializer,
        responses={
            200: RequestReadSerializer,
            404: OpenApiResponse(description="The request or eligible team mechanic is unavailable."),
            409: OpenApiResponse(description="The manager or mechanic has an active job, or the request was claimed."),
        },
        tags=["Manager"],
    )
    def post(self, request, request_id):
        role, manager = get_mobile_profile(request.user)
        if role != "manager":
            raise PermissionDenied("Only managers can claim service requests.")
        if not manager.is_email_verified:
            raise PermissionDenied("Verify your email before accessing manager tools.")
        if not manager.status:
            raise PermissionDenied("This manager profile is awaiting approval.")

        serializer = ManagerRequestClaimSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            service_request = claim_and_assign_request(
                manager=manager,
                request_id=request_id,
                mechanic_id=serializer.validated_data["mechanic_id"],
            )
        except Request.DoesNotExist:
            raise NotFound("This pending request is no longer available in your state.")
        except Mechanic.DoesNotExist:
            raise NotFound("Choose an approved, verified mechanic linked to your team.")
        except ManagerClaimConflict as conflict:
            return Response(
                {"detail": conflict.detail, "code": conflict.code},
                status=conflict.status_code,
            )

        return Response(RequestReadSerializer(service_request).data, status=status.HTTP_200_OK)
