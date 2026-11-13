from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from vehicle.models import Driver, Manager, Mechanic, Request

User = get_user_model()


def get_mobile_profile(user, *, for_authentication=False):
    profile_options = (
        ("driver", Driver),
        ("mechanic", Mechanic),
        ("manager", Manager),
    )
    profiles = [
        (role, profile_model.objects.filter(user=user).first())
        for role, profile_model in profile_options
    ]
    profiles = [(role, profile) for role, profile in profiles if profile is not None]

    error = AuthenticationFailed if for_authentication else PermissionDenied
    if len(profiles) != 1:
        raise error("This account does not have one eligible mobile profile.")

    return profiles[0]


class MobileUserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    is_email_verified = serializers.SerializerMethodField()
    is_approved = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_email_verified",
            "is_approved",
        )
        read_only_fields = fields

    def get_role(self, user) -> str:
        role, _ = get_mobile_profile(user)
        return role

    def get_is_email_verified(self, user) -> bool:
        _, profile = get_mobile_profile(user)
        return profile.is_email_verified

    def get_is_approved(self, user) -> bool:
        role, profile = get_mobile_profile(user)
        return role == "driver" or profile.status


class MobileTokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = MobileUserSerializer(read_only=True)


class MobileLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class MobileTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        get_mobile_profile(self.user, for_authentication=True)
        data["user"] = MobileUserSerializer(self.user).data
        return data


class RequestReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = (
            "id",
            "category",
            "vehicle_no",
            "vehicle_name",
            "location",
            "state",
            "latitude",
            "longitude",
            "mechanic_location",
            "status",
            "date",
            "estimated_completion_date",
            "eta",
            "problem_description",
            "currency",
            "cost",
            "tax",
        )
        read_only_fields = fields


class RequestCreateSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=Request._meta.get_field("category").choices)
    vehicle_no = serializers.CharField(max_length=150, trim_whitespace=True)
    vehicle_name = serializers.CharField(max_length=140, trim_whitespace=True)
    problem_description = serializers.CharField(max_length=500, trim_whitespace=True)
    state = serializers.CharField(max_length=255, trim_whitespace=True)
    location = serializers.CharField(max_length=255, trim_whitespace=True)
    mobile = serializers.CharField(max_length=40, trim_whitespace=True)
    latitude = serializers.FloatField(required=False, allow_null=True, min_value=-90, max_value=90)
    longitude = serializers.FloatField(required=False, allow_null=True, min_value=-180, max_value=180)

    def validate(self, attrs):
        latitude = attrs.get("latitude")
        longitude = attrs.get("longitude")
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError(
                {"latitude": "Provide latitude and longitude together, or omit both."}
            )
        return attrs


class MechanicRequestActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=("accept", "start", "complete"))


class NotificationReadSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    message = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    is_read = serializers.BooleanField(read_only=True)


class ManagerMechanicSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    union_name = serializers.CharField(allow_blank=True, allow_null=True)
    state = serializers.CharField(allow_blank=True, allow_null=True)
    local_government = serializers.CharField(allow_blank=True, allow_null=True)
    is_approved = serializers.BooleanField()
    can_be_assigned = serializers.BooleanField()
    assigned_request_count = serializers.IntegerField()
    active_request_count = serializers.IntegerField()


class ManagerMechanicPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = ManagerMechanicSummarySerializer(many=True)


class ManagerQueueRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = (
            "id",
            "category",
            "vehicle_no",
            "vehicle_name",
            "location",
            "state",
            "problem_description",
            "status",
            "date",
        )
        read_only_fields = fields


class ManagerRequestClaimSerializer(serializers.Serializer):
    mechanic_id = serializers.IntegerField(min_value=1)
