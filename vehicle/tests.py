from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from vehicle.models import (
    Driver,
    DriverNotification,
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
    def make_request(*, driver, mechanic=None, manager=None):
        return Request.objects.create(
            category="Tire Repair",
            vehicle_no="ABC-123",
            vehicle_name="Example vehicle",
            location="Ikeja",
            problem_description="Flat tire",
            driver=driver,
            mechanic=mechanic,
            manager=manager,
        )

    def authenticate_as(self, user):
        access_token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    def test_private_endpoints_require_authentication(self):
        self.assertEqual(self.client.get("/api/v1/me/").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/requests/").status_code, 401)
        self.assertEqual(self.client.get("/api/v1/notifications/").status_code, 401)
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

        self.assertEqual(response.status_code, 403)

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

    def test_refresh_rotates_and_logout_blacklists_refresh_token(self):
        login = self.client.post(
            "/api/v1/auth/login/",
            {"username": "driver-one", "password": "StrongPassword123!"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)
        original_refresh = login.data["refresh"]

        refreshed = self.client.post(
            "/api/v1/auth/refresh/", {"refresh": original_refresh}, format="json"
        )
        self.assertEqual(refreshed.status_code, 200)
        self.assertIn("refresh", refreshed.data)
        self.assertNotEqual(refreshed.data["refresh"], original_refresh)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refreshed.data['access']}")
        logout = self.client.post(
            "/api/v1/auth/logout/",
            {"refresh": refreshed.data["refresh"]},
            format="json",
        )
        self.assertEqual(logout.status_code, 204)

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

    def test_mobile_profile_and_request_collection_are_read_only(self):
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
        self.assertEqual(request_create.status_code, 405)
        self.assertEqual(request_update.status_code, 405)
