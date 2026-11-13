from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
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
    push_token = serializers.CharField(max_length=255, required=False, allow_blank=False)


class MobileDeviceTokenRegistrationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=255, trim_whitespace=True)
    platform = serializers.ChoiceField(choices=("ios", "android"))
    previous_token = serializers.CharField(max_length=255, required=False, allow_blank=False)

    def validate_token(self, value):
        if not (value.startswith(("ExpoPushToken[", "ExponentPushToken[")) and value.endswith("]")):
            raise serializers.ValidationError("Enter a valid Expo push token.")
        return value


class MobileDeviceTokenResponseSerializer(serializers.Serializer):
    registered = serializers.BooleanField(required=False)
    revoked = serializers.BooleanField(required=False)


MECHANIC_SERVICE_CHOICES = (
    "Tire Repair",
    "Towing Service",
    "Battery Jumpstart",
    "Electrical Issues",
    "Engine Repair",
    "Bodywork/Collision Repair",
    "Other Repair Service",
    "General Mechanics/All Services",
)


class MobileRegistrationSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=("driver", "mechanic"))
    first_name = serializers.CharField(max_length=150, trim_whitespace=True)
    last_name = serializers.CharField(max_length=150, trim_whitespace=True)
    username = serializers.CharField(
        max_length=150,
        trim_whitespace=True,
        validators=User._meta.get_field("username").validators,
    )
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(min_length=8, write_only=True, trim_whitespace=False)
    password_confirm = serializers.CharField(min_length=8, write_only=True, trim_whitespace=False)
    mobile = serializers.CharField(max_length=150, trim_whitespace=True)
    address = serializers.CharField(max_length=150, trim_whitespace=True, required=False, allow_blank=True)
    license_no = serializers.CharField(max_length=150, trim_whitespace=True, required=False, allow_blank=True)
    vehicle_model = serializers.CharField(max_length=150, trim_whitespace=True, required=False, allow_blank=True)
    state = serializers.CharField(max_length=100, trim_whitespace=True, required=False, allow_blank=True)
    local_government = serializers.CharField(max_length=100, trim_whitespace=True, required=False, allow_blank=True)
    union_name = serializers.CharField(max_length=150, trim_whitespace=True, required=False, allow_blank=True)
    union_location = serializers.CharField(max_length=150, trim_whitespace=True, required=False, allow_blank=True)
    services = serializers.ListField(
        child=serializers.ChoiceField(choices=MECHANIC_SERVICE_CHOICES),
        required=False,
        allow_empty=False,
    )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        if User.objects.filter(username__iexact=attrs["username"]).exists():
            raise serializers.ValidationError({"username": "This username is already in use."})
        if User.objects.filter(email__iexact=attrs["email"]).exists():
            raise serializers.ValidationError({"email": "An account with this email already exists."})

        user = User(
            username=attrs["username"],
            email=attrs["email"],
            first_name=attrs["first_name"],
            last_name=attrs["last_name"],
        )
        try:
            validate_password(attrs["password"], user=user)
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": list(error.messages)}) from error

        if attrs["role"] == "mechanic":
            missing_fields = [
                field
                for field in ("state", "local_government")
                if not attrs.get(field)
            ]
            if missing_fields:
                raise serializers.ValidationError(
                    {field: "This field is required for mechanic registration." for field in missing_fields}
                )
            if not attrs.get("services"):
                raise serializers.ValidationError({"services": "Select at least one service."})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        attrs = dict(validated_data)
        role = attrs.pop("role")
        password = attrs.pop("password")
        attrs.pop("password_confirm")
        services = attrs.pop("services", [])
        username = attrs.pop("username")
        email = attrs.pop("email").strip()
        first_name = attrs.pop("first_name")
        last_name = attrs.pop("last_name")
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        if role == "driver":
            Driver.objects.create(
                user=user,
                mobile=attrs["mobile"],
                address=attrs.get("address", ""),
                license_no=attrs.get("license_no", ""),
                vehicle_model=attrs.get("vehicle_model", ""),
            )
        else:
            Mechanic.objects.create(
                user=user,
                mobile=attrs["mobile"],
                address=attrs.get("address", ""),
                state=attrs.get("state", ""),
                local_government=attrs.get("local_government", ""),
                union_name=attrs.get("union_name", ""),
                union_location=attrs.get("union_location", ""),
                service=", ".join(services),
            )

        group, _ = Group.objects.get_or_create(name=role.upper())
        group.user_set.add(user)
        return user


class MobileRegistrationResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    role = serializers.ChoiceField(choices=("driver", "mechanic"))
    verification_required = serializers.BooleanField()


class MobileResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)


class MobileResendVerificationResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


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


class NotificationMarkAllReadResponseSerializer(serializers.Serializer):
    updated_count = serializers.IntegerField(read_only=True)


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
