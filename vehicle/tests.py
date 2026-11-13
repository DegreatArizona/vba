from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from vehicle.models import (
    Driver,
    DriverNotification,
    MobileDeviceToken,
    Manager,
    ManagerNotification,
    Mechanic,
    MechanicNotification,
    Request,
)


@override_settings(ALLOWED_HOSTS=["testserver"])
class MobileApiTests(TestCase):
    def setUp(self):
        self.driver_user = User.objects.create_user(
            username="driver-one", password="StrongPassword123!", email="driver@example.test"
        )
        self.driver = Driver.objects.create(
            user=self.driver_user,
            is_email_verified=True,
            mobile="+2348000000001",
        )
        self.other_driver_user = User.objects.create_user(
            username="driver-two", password="StrongPassword123!", email="driver2@example.test"
        )
        self.other_driver = Driver.objects.create(user=self.other_driver_user)

        self.mechanic_user = User.objects.create_user(
            username="mechanic-one", password="StrongPassword123!", email="mechanic@example.test"
        )
        self.mechanic = Mechanic.objects.create(
            user=self.mechanic_user,
            status=True,
            is_email_verified=True,
            account_number="1234567890",
        )
        self.other_mechanic_user = User.objects.create_user(
            username="mechanic-two", password="StrongPassword123!", email="mechanic2@example.test"
        )
        self.other_mechanic = Mechanic.objects.create(user=self.other_mechanic_user, status=True)

        self.manager_user = User.objects.create_user(
            username="manager-one", password="StrongPassword123!", email="manager@example.test"
        )
        self.manager = Manager.objects.create(
            user=self.manager_user,
            state="Lagos",
            local_government="Ikeja",
            status=True,
            is_email_verified=True,
        )
        self.other_manager_user = User.objects.create_user(
            username="manager-two", password="StrongPassword123!", email="manager2@example.test"
        )
        self.other_manager = Manager.objects.create(
            user=self.other_manager_user,
            state="Lagos",
            local_government="Surulere",
            status=True,
        )

        self.driver_request = self.make_request(driver=self.driver, mechanic=self.mechanic, manager=self.manager)
        self.other_driver_request = self.make_request(driver=self.other_driver)
        self.other_mechanic_request = self.make_request(
            driver=self.driver, mechanic=self.other_mechanic, manager=self.other_manager
        )
        self.client = APIClient()

    @staticmethod
    def make_request(*, driver, mechanic=None, manager=None, state=None, status="Pending"):
        return Request.objects.create(
            category="Tire Repair",
            vehicle_no="ABC-123",
            vehicle_name="Example vehicle",
            location="Ikeja",
            problem_description="Flat tire",
            driver=driver,
            mechanic=mechanic,
            manager=manager,
            state=state,
            status=status,
        )

    def authenticate_as(self, user):
        access_token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    def test_private_endpoints_require_authentication(self):
        self.assertEqual(self.client.get("/api/v1/me/").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/requests/").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/notifications/").status_code, 401)
        self.assertEqual(self.client.post("/api/v1/notifications/read-all/").status_code, 401)
        self.assertEqual(self.client.post("/api/v1/notifications/1/read/").status_code, 401)
        self.assertEqual(
            self.client.post(
                "/api/v1/push-tokens/register/",
                {"token": "ExpoPushToken[test-device]", "platform": "ios"},
                format="json",
            ).status_code,
            401,
        )
        self.assertEqual(self.client.get("/api/v1/manager/mechanics/").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/manager/queue/").status_code, 401)
        self.assertEqual(
            self.client.post(
                "/api/v1/manager/queue/1/claim/",
                {"mechanic_id": 1},
                format="json",
            ).status_code,
            401,
        )
        self.assertEqual(
            self.client.post(
                "/api/v1/requests/1/actions/",
                {"action": "accept"},
                format="json",
            ).status_code,
            401,
        )
        self.assertEqual(
            self.client.get(f"/api/v1/requests/{self.driver_request.pk}/").status_code,
            401,
        )

    def test_login_returns_role_and_short_lived_token_pair(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"username": "driver-one", "password": "StrongPassword123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["role"], "driver")
        self.assertTrue(response.data["user"]["is_email_verified"])

    def test_accounts_without_one_mobile_profile_cannot_log_in(self):
        User.objects.create_user(username="staff-only", password="StrongPassword123!")
        response = self.client.post(
            "/api/v1/auth/login/",
            {"username": "staff-only", "password": "StrongPassword123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        SITE_URL="https://autoaid.example.test",
    )
    def test_driver_registration_creates_unverified_account_and_sends_verification_email(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "role": "driver",
                "first_name": "New",
                "last_name": "Driver",
                "username": "new-driver",
                "email": "new-driver@example.test",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "mobile": "+2348000000099",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["role"], "driver")
        self.assertTrue(response.data["verification_required"])
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        user = User.objects.get(username="new-driver")
        driver = Driver.objects.get(user=user)
        self.assertTrue(user.check_password("StrongPassword123!"))
        self.assertFalse(driver.is_email_verified)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("https://autoaid.example.test/verify-email/", mail.outbox[0].alternatives[0][0])

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_mechanic_registration_requires_service_area_and_starts_pending(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "role": "mechanic",
                "first_name": "New",
                "last_name": "Mechanic",
                "username": "new-mechanic",
                "email": "new-mechanic@example.test",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "mobile": "+2348000000088",
                "state": "Lagos",
                "local_government": "Ikeja",
                "services": ["Tire Repair", "Engine Repair"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        mechanic = Mechanic.objects.get(user__username="new-mechanic")
        self.assertFalse(mechanic.status)
        self.assertFalse(mechanic.is_email_verified)
        self.assertEqual(mechanic.service, "Tire Repair, Engine Repair")

        invalid_response = self.client.post(
            "/api/v1/auth/register/",
            {
                "role": "mechanic",
                "first_name": "Missing",
                "last_name": "Area",
                "username": "missing-area",
                "email": "missing-area@example.test",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "mobile": "+2348000000077",
                "services": ["Tire Repair"],
            },
            format="json",
        )
        self.assertEqual(invalid_response.status_code, 400)
        self.assertFalse(User.objects.filter(username="missing-area").exists())

    def test_mobile_registration_does_not_allow_manager_accounts(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "role": "manager",
                "first_name": "New",
                "last_name": "Manager",
                "username": "new-manager",
                "email": "new-manager@example.test",
                "password": "StrongPassword123!",
                "password_confirm": "StrongPassword123!",
                "mobile": "+2348000000066",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username="new-manager").exists())

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        SITE_URL="https://autoaid.example.test",
    )
    def test_resend_verification_uses_a_generic_response_for_existing_and_unknown_email(self):
        existing_response = self.client.post(
            "/api/v1/auth/resend-verification/",
            {"email": self.other_driver_user.email},
            format="json",
        )
        unknown_response = self.client.post(
            "/api/v1/auth/resend-verification/",
            {"email": "not-registered@example.test"},
            format="json",
        )

        self.assertEqual(existing_response.status_code, 202)
        self.assertEqual(unknown_response.status_code, 202)
        self.assertEqual(existing_response.data, unknown_response.data)
        self.assertEqual(len(mail.outbox), 1)

    def test_profile_response_does_not_expose_banking_fields(self):
        self.authenticate_as(self.mechanic_user)
        response = self.client.get("/api/v1/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role"], "mechanic")
        self.assertNotIn("account_number", response.data)
        self.assertNotIn("mobile", response.data)

    def test_driver_sees_only_own_requests(self):
        self.authenticate_as(self.driver_user)
        response = self.client.get("/api/v1/requests/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {row["id"] for row in response.data["results"]},
            {self.driver_request.pk, self.other_mechanic_request.pk},
        )
        self.assertNotIn("transaction_reference", response.data["results"][0])

    def test_mechanic_sees_only_assigned_requests(self):
        self.authenticate_as(self.mechanic_user)
        response = self.client.get("/api/v1/requests/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.data["results"]], [self.driver_request.pk])

    def test_manager_sees_only_requests_assigned_to_that_manager(self):
        self.authenticate_as(self.manager_user)
        response = self.client.get("/api/v1/requests/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.data["results"]], [self.driver_request.pk])

    def test_driver_notifications_are_profile_scoped(self):
        own = DriverNotification.objects.create(driver=self.driver, message="Driver update")
        DriverNotification.objects.create(driver=self.other_driver, message="Private update")
        self.authenticate_as(self.driver_user)

        response = self.client.get("/api/v1/notifications/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual([row["id"] for row in response.data["results"]], [own.pk])
        self.assertEqual(
            set(response.data["results"][0]),
            {"id", "message", "timestamp", "is_read"},
        )
        self.assertFalse(response.data["results"][0]["is_read"])
        own.refresh_from_db()
        self.assertFalse(own.is_read)

    def test_mechanic_notifications_are_profile_scoped(self):
        own = MechanicNotification.objects.create(mechanic=self.mechanic, message="Job update")
        MechanicNotification.objects.create(mechanic=self.other_mechanic, message="Private job update")
        self.authenticate_as(self.mechanic_user)

        response = self.client.get("/api/v1/notifications/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.data["results"]], [own.pk])

    def test_manager_notifications_are_profile_scoped(self):
        own = ManagerNotification.objects.create(manager=self.manager, message="Team update")
        ManagerNotification.objects.create(manager=self.other_manager, message="Private team update")
        self.authenticate_as(self.manager_user)

        response = self.client.get("/api/v1/notifications/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.data["results"]], [own.pk])

    def test_unverified_and_pending_profiles_can_read_onboarding_notifications(self):
        unverified_user = User.objects.create_user(
            username="unverified-notifications", password="StrongPassword123!"
        )
        unverified_driver = Driver.objects.create(user=unverified_user, is_email_verified=False)
        driver_notification = DriverNotification.objects.create(
            driver=unverified_driver,
            message="Verify your email address.",
        )
        self.authenticate_as(unverified_user)
        driver_response = self.client.get("/api/v1/notifications/")

        pending_user = User.objects.create_user(
            username="pending-notifications", password="StrongPassword123!"
        )
        pending_mechanic = Mechanic.objects.create(
            user=pending_user,
            is_email_verified=True,
            status=False,
        )
        mechanic_notification = MechanicNotification.objects.create(
            mechanic=pending_mechanic,
            message="Your mechanic profile is under review.",
        )
        self.authenticate_as(pending_user)
        mechanic_response = self.client.get("/api/v1/notifications/")

        self.assertEqual(driver_response.status_code, 200)
        self.assertEqual([row["id"] for row in driver_response.data["results"]], [driver_notification.pk])
        self.assertEqual(mechanic_response.status_code, 200)
        self.assertEqual([row["id"] for row in mechanic_response.data["results"]], [mechanic_notification.pk])

    def test_accounts_without_one_mobile_profile_cannot_read_notifications(self):
        staff_user = User.objects.create_user(
            username="notification-staff-only", password="StrongPassword123!"
        )
        self.authenticate_as(staff_user)

        response = self.client.get("/api/v1/notifications/")
        push_response = self.client.post(
            "/api/v1/push-tokens/register/",
            {"token": "ExpoPushToken[staff-device]", "platform": "ios"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(push_response.status_code, 403)

    def test_notification_list_does_not_support_writes(self):
        notification = DriverNotification.objects.create(driver=self.driver, message="Unread update")
        self.authenticate_as(self.driver_user)

        create_response = self.client.post(
            "/api/v1/notifications/",
            {"message": "Injected update"},
            format="json",
        )
        update_response = self.client.patch(
            "/api/v1/notifications/",
            {"is_read": True},
            format="json",
        )
        notification.refresh_from_db()

        self.assertEqual(create_response.status_code, 405)
        self.assertEqual(update_response.status_code, 405)
        self.assertFalse(notification.is_read)

    def test_users_can_mark_only_their_own_notifications_as_read(self):
        own = DriverNotification.objects.create(driver=self.driver, message="Read this update")
        other = DriverNotification.objects.create(driver=self.other_driver, message="Private update")
        self.authenticate_as(self.driver_user)

        response = self.client.post(f"/api/v1/notifications/{own.pk}/read/", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_read"])

        response = self.client.post(f"/api/v1/notifications/{other.pk}/read/", format="json")
        other.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertFalse(other.is_read)

    def test_all_mobile_roles_can_mark_their_own_notifications_as_read(self):
        notifications = (
            (self.driver_user, DriverNotification.objects.create(driver=self.driver, message="Driver update")),
            (self.mechanic_user, MechanicNotification.objects.create(mechanic=self.mechanic, message="Mechanic update")),
            (self.manager_user, ManagerNotification.objects.create(manager=self.manager, message="Manager update")),
        )

        for user, notification in notifications:
            with self.subTest(role=user.username):
                self.authenticate_as(user)
                response = self.client.post(f"/api/v1/notifications/{notification.pk}/read/", format="json")
                notification.refresh_from_db()
                self.assertEqual(response.status_code, 200)
                self.assertTrue(notification.is_read)

    def test_mark_all_notifications_is_scoped_to_the_current_profile(self):
        own_first = DriverNotification.objects.create(driver=self.driver, message="First update")
        own_second = DriverNotification.objects.create(driver=self.driver, message="Second update")
        other = DriverNotification.objects.create(driver=self.other_driver, message="Private update")
        self.authenticate_as(self.driver_user)

        response = self.client.post("/api/v1/notifications/read-all/", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"updated_count": 2})

        own_first.refresh_from_db()
        own_second.refresh_from_db()
        other.refresh_from_db()
        self.assertTrue(own_first.is_read)
        self.assertTrue(own_second.is_read)
        self.assertFalse(other.is_read)

        repeated_response = self.client.post("/api/v1/notifications/read-all/", format="json")
        self.assertEqual(repeated_response.data, {"updated_count": 0})

    def test_driver_can_retrieve_own_request(self):
        self.authenticate_as(self.driver_user)
        response = self.client.get(f"/api/v1/requests/{self.driver_request.pk}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.driver_request.pk)

    def test_driver_cannot_retrieve_another_drivers_request(self):
        self.authenticate_as(self.driver_user)
        response = self.client.get(f"/api/v1/requests/{self.other_driver_request.pk}/")

        self.assertEqual(response.status_code, 404)

    def test_mechanic_and_manager_can_retrieve_only_assigned_requests(self):
        self.authenticate_as(self.mechanic_user)
        allowed = self.client.get(f"/api/v1/requests/{self.driver_request.pk}/")
        denied = self.client.get(f"/api/v1/requests/{self.other_driver_request.pk}/")
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(denied.status_code, 404)

        self.authenticate_as(self.manager_user)
        allowed = self.client.get(f"/api/v1/requests/{self.driver_request.pk}/")
        denied = self.client.get(f"/api/v1/requests/{self.other_driver_request.pk}/")
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(denied.status_code, 404)

    def test_unverified_driver_cannot_retrieve_request_details(self):
        unverified_user = User.objects.create_user(
            username="unverified-detail-driver", password="StrongPassword123!"
        )
        Driver.objects.create(user=unverified_user, is_email_verified=False)
        self.authenticate_as(unverified_user)

        response = self.client.get(f"/api/v1/requests/{self.driver_request.pk}/")

        self.assertEqual(response.status_code, 403)

    def test_push_token_registration_is_idempotent_and_rotates_previous_token(self):
        self.authenticate_as(self.driver_user)
        first_response = self.client.post(
            "/api/v1/push-tokens/register/",
            {"token": "ExpoPushToken[first-device-token]", "platform": "ios"},
            format="json",
        )
        self.assertEqual(first_response.status_code, 200)
        first_token = MobileDeviceToken.objects.get(expo_push_token="ExpoPushToken[first-device-token]")

        repeated_response = self.client.post(
            "/api/v1/push-tokens/register/",
            {"token": first_token.expo_push_token, "platform": "ios"},
            format="json",
        )
        self.assertEqual(repeated_response.status_code, 200)
        self.assertEqual(MobileDeviceToken.objects.count(), 1)

        rotated_response = self.client.post(
            "/api/v1/push-tokens/register/",
            {
                "token": "ExpoPushToken[rotated-device-token]",
                "platform": "ios",
                "previous_token": first_token.expo_push_token,
            },
            format="json",
        )
        first_token.refresh_from_db()
        rotated_token = MobileDeviceToken.objects.get(expo_push_token="ExpoPushToken[rotated-device-token]")

        self.assertEqual(rotated_response.status_code, 200)
        self.assertFalse(first_token.is_active)
        self.assertTrue(rotated_token.is_active)
        self.assertEqual(MobileDeviceToken.objects.count(), 2)

    def test_refresh_rotates_and_logout_blacklists_refresh_token(self):
        login = self.client.post(
            "/api/v1/auth/login/",
            {"username": "driver-one", "password": "StrongPassword123!"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)
        original_refresh = login.data["refresh"]
        push_device = MobileDeviceToken.objects.create(
            user=self.driver_user,
            expo_push_token="ExpoPushToken[driver-device]",
            platform="ios",
        )

        refreshed = self.client.post(
            "/api/v1/auth/refresh/", {"refresh": original_refresh}, format="json"
        )
        self.assertEqual(refreshed.status_code, 200)
        self.assertIn("refresh", refreshed.data)
        self.assertNotEqual(refreshed.data["refresh"], original_refresh)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refreshed.data['access']}")
        logout = self.client.post(
            "/api/v1/auth/logout/",
            {
                "refresh": refreshed.data["refresh"],
                "push_token": push_device.expo_push_token,
            },
            format="json",
        )
        self.assertEqual(logout.status_code, 204)
        push_device.refresh_from_db()
        self.assertFalse(push_device.is_active)

        rejected = self.client.post(
            "/api/v1/auth/refresh/",
            {"refresh": refreshed.data["refresh"]},
            format="json",
        )
        self.assertIn(rejected.status_code, (400, 401))

    def test_unverified_driver_cannot_read_requests(self):
        unverified_user = User.objects.create_user(
            username="unverified-driver", password="StrongPassword123!"
        )
        Driver.objects.create(user=unverified_user, is_email_verified=False)
        self.authenticate_as(unverified_user)

        response = self.client.get("/api/v1/requests/")

        self.assertEqual(response.status_code, 403)

    def test_unapproved_mechanic_cannot_read_requests(self):
        pending_user = User.objects.create_user(
            username="pending-mechanic", password="StrongPassword123!"
        )
        Mechanic.objects.create(
            user=pending_user, is_email_verified=True, status=False
        )
        self.authenticate_as(pending_user)

        response = self.client.get("/api/v1/requests/")

        self.assertEqual(response.status_code, 403)

    def test_profile_and_request_detail_updates_are_read_only(self):
        self.authenticate_as(self.driver_user)

        profile_update = self.client.patch(
            "/api/v1/me/", {"email": "changed@example.test"}, format="json"
        )
        request_create = self.client.post(
            "/api/v1/requests/", {"category": "Tire Repair"}, format="json"
        )
        request_update = self.client.patch(
            f"/api/v1/requests/{self.driver_request.pk}/",
            {"status": "Done"},
            format="json",
        )

        self.assertEqual(profile_update.status_code, 405)
        self.assertEqual(request_create.status_code, 400)
        self.assertEqual(request_update.status_code, 405)

    def test_verified_driver_can_create_a_pending_request_without_client_controlled_fields(self):
        outside_state_user = User.objects.create_user(
            username="manager-outside-state", password="StrongPassword123!"
        )
        outside_state_manager = Manager.objects.create(
            user=outside_state_user,
            state="Ogun",
            status=True,
            is_email_verified=True,
        )
        for existing_request in (self.driver_request, self.other_mechanic_request):
            existing_request.status = "Released"
            existing_request.invoice = "Paid"
            existing_request.save(update_fields=["status", "invoice"])
        self.authenticate_as(self.driver_user)
        payload = {
            "category": "Tire Repair",
            "vehicle_no": "ABC-123",
            "vehicle_name": "Toyota Corolla",
            "problem_description": "A flat tire on the rear passenger side.",
            "state": "Lagos",
            "location": "Victoria Island, near the waterfront",
            "mobile": "+2348000000001",
            "status": "Approved",
            "driver": self.other_driver.pk,
            "manager": self.manager.pk,
            "cost": 999999,
            "invoice": "Paid",
        }

        with patch("vehicle.request_services.dispatch_request_created_notifications") as dispatch:
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                response = self.client.post("/api/v1/requests/", payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(callbacks), 1)
        created = Request.objects.get(pk=response.data["id"])
        dispatch.assert_called_once_with(created.pk)
        self.assertEqual(created.driver, self.driver)
        self.assertEqual(created.status, "Pending")
        self.assertEqual(created.cost, 0)
        self.assertEqual(created.invoice, "Pending")
        self.assertIsNone(created.manager)
        self.assertIsNone(created.latitude)
        self.assertIsNone(created.longitude)
        self.assertEqual(
            DriverNotification.objects.filter(driver=self.driver).count(),
            1,
        )
        self.assertTrue(
            ManagerNotification.objects.filter(
                manager=self.manager,
                message__contains=f"request #{created.pk}",
            ).exists()
        )
        self.assertFalse(
            ManagerNotification.objects.filter(manager=self.other_manager).exists()
        )
        self.assertFalse(
            ManagerNotification.objects.filter(manager=outside_state_manager).exists()
        )

    def test_driver_request_creation_rejects_active_requests_and_invalid_categories(self):
        self.authenticate_as(self.driver_user)
        payload = {
            "category": "Tire Repair",
            "vehicle_no": "ABC-123",
            "vehicle_name": "Toyota Corolla",
            "problem_description": "A flat tire on the rear passenger side.",
            "state": "Lagos",
            "location": "Victoria Island, near the waterfront",
            "mobile": "+2348000000001",
        }

        conflict = self.client.post("/api/v1/requests/", payload, format="json")
        invalid = self.client.post(
            "/api/v1/requests/",
            {**payload, "category": "An unsupported service"},
            format="json",
        )

        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.data["code"], "active_request")
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(Request.objects.filter(driver=self.driver).count(), 2)

    def test_only_verified_drivers_can_create_requests(self):
        payload = {
            "category": "Tire Repair",
            "vehicle_no": "ABC-123",
            "vehicle_name": "Toyota Corolla",
            "problem_description": "A flat tire on the rear passenger side.",
            "state": "Lagos",
            "location": "Victoria Island, near the waterfront",
            "mobile": "+2348000000001",
        }

        for user in (self.mechanic_user, self.manager_user, self.other_driver_user):
            self.authenticate_as(user)
            response = self.client.post("/api/v1/requests/", payload, format="json")
            self.assertEqual(response.status_code, 403)

        self.assertEqual(Request.objects.count(), 3)

    def test_assigned_mechanic_can_accept_start_and_complete_without_changing_price(self):
        self.driver_request.status = "Approved"
        self.driver_request.cost = 1250
        self.driver_request.save(update_fields=["status", "cost"])
        original_cost = self.driver_request.cost
        self.authenticate_as(self.mechanic_user)

        with patch("vehicle.request_services.dispatch_mechanic_action_notifications") as dispatch:
            for action, expected_status in (
                ("accept", "Accepted"),
                ("start", "Repairing"),
                ("complete", "Done"),
            ):
                with self.captureOnCommitCallbacks(execute=True) as callbacks:
                    response = self.client.post(
                        f"/api/v1/requests/{self.driver_request.pk}/actions/",
                        {"action": action},
                        format="json",
                    )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["status"], expected_status)
                self.assertEqual(len(callbacks), 1)

        self.driver_request.refresh_from_db()
        self.assertEqual(self.driver_request.status, "Done")
        self.assertEqual(self.driver_request.cost, original_cost)
        self.assertIsNotNone(self.driver_request.estimated_completion_date)
        self.assertEqual(dispatch.call_count, 3)
        self.assertEqual(MechanicNotification.objects.filter(mechanic=self.mechanic).count(), 3)
        self.assertEqual(DriverNotification.objects.filter(driver=self.driver).count(), 3)

    def test_mechanic_actions_are_scoped_and_require_valid_transitions(self):
        self.authenticate_as(self.mechanic_user)
        response = self.client.post(
            f"/api/v1/requests/{self.other_mechanic_request.pk}/actions/",
            {"action": "accept"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

        self.driver_request.status = "Approved"
        self.driver_request.save(update_fields=["status"])
        response = self.client.post(
            f"/api/v1/requests/{self.driver_request.pk}/actions/",
            {"action": "complete"},
            format="json",
        )
        self.assertEqual(response.status_code, 409)
        self.driver_request.refresh_from_db()
        self.assertEqual(self.driver_request.status, "Approved")

    def test_mechanic_actions_require_an_approved_verified_mechanic(self):
        self.mechanic.status = False
        self.mechanic.save(update_fields=["status"])
        self.authenticate_as(self.mechanic_user)
        response = self.client.post(
            f"/api/v1/requests/{self.driver_request.pk}/actions/",
            {"action": "accept"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

        self.mechanic.status = True
        self.mechanic.is_email_verified = False
        self.mechanic.save(update_fields=["status", "is_email_verified"])
        response = self.client.post(
            f"/api/v1/requests/{self.driver_request.pk}/actions/",
            {"action": "accept"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_manager_team_is_scoped_and_returns_only_safe_profile_data(self):
        self.mechanic.my_manager = self.manager
        self.mechanic.save(update_fields=["my_manager"])
        self.other_mechanic.my_manager = self.other_manager
        self.other_mechanic.save(update_fields=["my_manager"])
        self.driver_request.status = "Repairing"
        self.driver_request.save(update_fields=["status"])
        self.authenticate_as(self.manager_user)

        response = self.client.get("/api/v1/manager/mechanics/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        mechanic = response.data["results"][0]
        self.assertEqual(mechanic["id"], self.mechanic.pk)
        self.assertTrue(mechanic["is_approved"])
        self.assertFalse(mechanic["can_be_assigned"])
        self.assertEqual(mechanic["assigned_request_count"], 1)
        self.assertEqual(mechanic["active_request_count"], 1)
        self.assertNotIn("mobile", mechanic)
        self.assertNotIn("account_number", mechanic)
        self.assertNotIn("business_license", mechanic)

    def test_manager_team_requires_verified_and_approved_manager(self):
        self.authenticate_as(self.manager_user)
        self.manager.status = False
        self.manager.save(update_fields=["status"])
        response = self.client.get("/api/v1/manager/mechanics/")
        self.assertEqual(response.status_code, 403)

        self.manager.status = True
        self.manager.is_email_verified = False
        self.manager.save(update_fields=["status", "is_email_verified"])
        response = self.client.get("/api/v1/manager/mechanics/")
        self.assertEqual(response.status_code, 403)

    def test_manager_queue_only_returns_unassigned_pending_requests_in_same_state(self):
        in_state = self.make_request(driver=self.other_driver, state="lAgOs")
        self.make_request(driver=self.other_driver, state="Ogun")
        self.make_request(driver=self.other_driver, manager=self.other_manager, state="Lagos")
        self.make_request(driver=self.other_driver, mechanic=self.other_mechanic, state="Lagos")
        self.make_request(driver=self.other_driver, state="Lagos", status="Accepted")
        self.authenticate_as(self.manager_user)

        response = self.client.get("/api/v1/manager/queue/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        queued_request = response.data["results"][0]
        self.assertEqual(queued_request["id"], in_state.pk)
        self.assertEqual(queued_request["state"], "lAgOs")
        self.assertNotIn("mobile", queued_request)
        self.assertNotIn("cost", queued_request)
        self.assertNotIn("driver", queued_request)

    def test_manager_can_claim_and_assign_a_state_request_atomically(self):
        self.mechanic.my_manager = self.manager
        self.mechanic.save(update_fields=["my_manager"])
        queue_request = self.make_request(driver=self.other_driver, state="lagos")
        self.authenticate_as(self.manager_user)

        response = self.client.post(
            f"/api/v1/manager/queue/{queue_request.pk}/claim/",
            {"mechanic_id": self.mechanic.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "Accepted")
        queue_request.refresh_from_db()
        self.assertEqual(queue_request.manager, self.manager)
        self.assertEqual(queue_request.mechanic, self.mechanic)
        self.assertEqual(queue_request.status, "Accepted")
        self.assertEqual(queue_request.cost, 0)
        self.assertEqual(queue_request.invoice, "Pending")
        self.assertTrue(
            ManagerNotification.objects.filter(
                manager=self.manager,
                message__contains=f"request #{queue_request.pk}",
            ).exists()
        )
        self.assertTrue(
            MechanicNotification.objects.filter(
                mechanic=self.mechanic,
                message__contains=f"request #{queue_request.pk}",
            ).exists()
        )
        self.assertTrue(
            DriverNotification.objects.filter(
                driver=self.other_driver,
                message__contains="assigned to a mechanic",
            ).exists()
        )

    def test_manager_claim_rejects_wrong_state_and_non_team_mechanic(self):
        self.authenticate_as(self.manager_user)
        queue_request = self.make_request(driver=self.other_driver, state="Ogun")
        wrong_state = self.client.post(
            f"/api/v1/manager/queue/{queue_request.pk}/claim/",
            {"mechanic_id": self.mechanic.pk},
            format="json",
        )
        self.assertEqual(wrong_state.status_code, 404)

        queue_request.state = "Lagos"
        queue_request.save(update_fields=["state"])
        not_on_team = self.client.post(
            f"/api/v1/manager/queue/{queue_request.pk}/claim/",
            {"mechanic_id": self.other_mechanic.pk},
            format="json",
        )
        self.assertEqual(not_on_team.status_code, 404)
        queue_request.refresh_from_db()
        self.assertIsNone(queue_request.manager)
        self.assertIsNone(queue_request.mechanic)
        self.assertEqual(queue_request.status, "Pending")

    def test_manager_and_mechanic_active_assignments_block_claims(self):
        self.mechanic.my_manager = self.manager
        self.mechanic.save(update_fields=["my_manager"])
        queue_request = self.make_request(driver=self.other_driver, state="Lagos")
        self.driver_request.status = "Accepted"
        self.driver_request.save(update_fields=["status"])
        self.authenticate_as(self.manager_user)

        manager_busy = self.client.post(
            f"/api/v1/manager/queue/{queue_request.pk}/claim/",
            {"mechanic_id": self.mechanic.pk},
            format="json",
        )
        self.assertEqual(manager_busy.status_code, 409)

        self.driver_request.status = "Pending"
        self.driver_request.save(update_fields=["status"])
        self.make_request(
            driver=self.other_driver,
            manager=self.other_manager,
            mechanic=self.mechanic,
            state="Lagos",
            status="Repairing",
        )
        mechanic_busy = self.client.post(
            f"/api/v1/manager/queue/{queue_request.pk}/claim/",
            {"mechanic_id": self.mechanic.pk},
            format="json",
        )
        self.assertEqual(mechanic_busy.status_code, 409)

    def test_public_schema_is_limited_to_mobile_v1_paths(self):
        response = self.client.get("/api/v1/schema/")

        self.assertEqual(response.status_code, 200)
        schema = response.data
        self.assertEqual(schema["info"]["version"], "1.0.0")
        self.assertIn({"url": "/api/v1", "description": "Mobile API v1"}, schema["servers"])

        paths = {path.rstrip("/") for path in schema["paths"]}
        for path in (
            "/auth/login",
            "/auth/refresh",
            "/auth/logout",
            "/me",
            "/requests",
            "/manager/mechanics",
            "/manager/queue",
            "/notifications",
        ):
            self.assertIn(path, paths)

        self.assertTrue(any(path.startswith("/requests/{") for path in paths))
        self.assertIn("get", schema["paths"]["/manager/mechanics/"])
        self.assertIn("get", schema["paths"]["/manager/queue/"])
        self.assertIn("post", schema["paths"]["/manager/queue/{request_id}/claim/"])
        self.assertIn("post", schema["paths"]["/requests/"])
        self.assertIn(
            "application/json",
            schema["paths"]["/requests/"]["post"]["requestBody"]["content"],
        )
        login_response = schema["paths"]["/auth/login/"]["post"]["responses"]["200"]
        self.assertIn("application/json", login_response["content"])
        self.assertIn(
            "user",
            schema["components"]["schemas"]["MobileTokenResponse"]["properties"],
        )
        self.assertEqual(
            schema["components"]["schemas"]["MobileUser"]["properties"]["is_email_verified"]["type"],
            "boolean",
        )
        self.assertNotIn("/schema", paths)
        self.assertFalse(any(path.startswith("/admin") for path in paths))
        self.assertFalse(any(path.startswith("/accounts") for path in paths))
