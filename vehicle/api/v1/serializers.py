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

    def get_role(self, user):
        role, _ = get_mobile_profile(user)
        return role

    def get_is_email_verified(self, user):
        _, profile = get_mobile_profile(user)
        return profile.is_email_verified

    def get_is_approved(self, user):
        role, profile = get_mobile_profile(user)
        return role == "driver" or profile.status


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


class NotificationReadSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    message = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    is_read = serializers.BooleanField(read_only=True)
