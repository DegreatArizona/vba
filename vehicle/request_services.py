import logging
from functools import partial

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (
    Driver,
    DriverNotification,
    Manager,
    ManagerNotification,
    Mechanic,
    MechanicNotification,
    Request,
)
from .utils import send_html_email

logger = logging.getLogger(__name__)


class RequestCreationConflict(Exception):
    def __init__(self, detail, code):
        self.detail = detail
        self.code = code
        super().__init__(detail)


def create_driver_request(*, driver, values):
    allowed_fields = {
        "category",
        "vehicle_no",
        "vehicle_name",
        "problem_description",
        "state",
        "location",
        "mobile",
        "latitude",
        "longitude",
    }
    request_values = {key: value for key, value in values.items() if key in allowed_fields}
    request_values["latitude"] = values.get("latitude")
    request_values["longitude"] = values.get("longitude")

    with transaction.atomic():
        locked_driver = Driver.objects.select_for_update().select_related("user").get(pk=driver.pk)
        blocking_statuses = (
            ("Pending", "You have a pending request", "active_request"),
            ("Approved", "You have an approved request", "active_request"),
            ("Accepted", "You have a request in repair", "active_request"),
            ("Repairing", "You have a request in repair", "active_request"),
            (
                "Done",
                "Please pay off any pending invoice before requesting new service",
                "pending_invoice",
            ),
        )

        for status_value, detail, code in blocking_statuses:
            if Request.objects.filter(driver=locked_driver, status=status_value).exists():
                raise RequestCreationConflict(detail, code)

        if Request.objects.filter(driver=locked_driver, invoice="Pending").exists():
            raise RequestCreationConflict(
                "Please pay off any pending invoice before requesting new service",
                "pending_invoice",
            )

        service_request = Request.objects.create(
            **request_values,
            driver=locked_driver,
            status="Pending",
            cost=0,
            invoice="Pending",
        )
        DriverNotification.objects.create(
            driver=locked_driver,
            message=(
                f"Request for {service_request.category} at {service_request.location} "
                f"has been created and is waiting for a manager in {service_request.state} to claim it."
            ),
        )
        eligible_managers = Manager.objects.filter(
            status=True,
            is_email_verified=True,
            state__iexact=(service_request.state or "").strip(),
        ).values_list("pk", flat=True)
        ManagerNotification.objects.bulk_create(
            [
                ManagerNotification(
                    manager_id=manager_id,
                    message=(
                        f"New request #{service_request.pk} is available in the "
                        f"{service_request.state} queue."
                    ),
                )
                for manager_id in eligible_managers
            ]
        )
        transaction.on_commit(
            partial(dispatch_request_created_notifications, service_request.pk)
        )

    return service_request


def dispatch_request_created_notifications(request_id):
    try:
        service_request = Request.objects.select_related("driver__user").get(pk=request_id)
    except Request.DoesNotExist:
        logger.exception("Created request %s disappeared before notification dispatch", request_id)
        return

    driver = service_request.driver
    if driver.user.email:
        _run_optional_effect(
            request_id,
            "driver email",
            partial(
                send_html_email,
                subject="Request Sent Successfully",
                template_name="mails/request_posted.html",
                context={"user": driver.user, "request": service_request},
                recipient_list=[driver.user.email],
            ),
        )

    admin_email = getattr(settings, "EMAIL_HOST_NAME", "")
    if admin_email:
        _run_optional_effect(
            request_id,
            "admin email",
            partial(
                send_html_email,
                subject="New Request Posted",
                template_name="mails/new_user_request.html",
                context={"user": driver.user, "request": service_request},
                recipient_list=[admin_email],
            ),
        )

    sms_api_key = getattr(settings, "TERMII_SMS_API", "")
    sms_base_url = getattr(settings, "TERMII_BASE_URL", "")
    manager_state = (service_request.state or "").strip()
    if not sms_api_key or not sms_base_url or not manager_state:
        return

    for manager in (
        Manager.objects.filter(
            status=True,
            is_email_verified=True,
            state__iexact=manager_state,
        )
        .exclude(mobile__isnull=True)
        .exclude(mobile="")
    ):
        payload = {
            "to": manager.mobile,
            "from": "Auto Aid",
            "sms": (
                f"Hello manager! A new request with ID {service_request.pk} at "
                f"{service_request.location} by {driver.user.first_name} "
                f"{driver.user.last_name} was posted. Review and assign the request."
            ),
            "type": "plain",
            "channel": "generic",
            "api_key": sms_api_key,
        }
        _run_optional_effect(
            request_id,
            "manager SMS",
            partial(
                requests.post,
                f"{sms_base_url.rstrip('/')}/api/sms/send/bulk",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=5,
            ),
        )


def _run_optional_effect(request_id, effect_name, effect):
    try:
        effect()
    except Exception:
        logger.exception("Failed to send %s for service request %s", effect_name, request_id)


class MechanicActionConflict(Exception):
    def __init__(self, detail, code="invalid_transition"):
        self.detail = detail
        self.code = code
        super().__init__(detail)


def perform_mechanic_request_action(*, mechanic, request_id, action):
    with transaction.atomic():
        locked_mechanic = Mechanic.objects.select_for_update().get(pk=mechanic.pk)
        service_request = Request.objects.select_for_update().select_related(
            "driver__user"
        ).get(pk=request_id, mechanic=locked_mechanic)

        update_fields = ["status"]
        if action == "accept":
            if service_request.status != "Approved":
                raise MechanicActionConflict("Only approved assignments can be accepted.")
            has_other_active_job = Request.objects.filter(
                mechanic=locked_mechanic,
                status__in=("Accepted", "Repairing", "Done"),
            ).exclude(pk=service_request.pk).exists()
            if has_other_active_job:
                raise MechanicActionConflict(
                    "Finish your current active job before accepting another assignment.",
                    "active_job",
                )
            service_request.status = "Accepted"
            action_text = "accepted"
            driver_text = "A mechanic accepted your request."
        elif action == "start":
            if service_request.status != "Accepted":
                raise MechanicActionConflict("Accept this assignment before starting work.")
            service_request.status = "Repairing"
            action_text = "started work on"
            driver_text = "The mechanic has started work on your request."
        elif action == "complete":
            if service_request.status != "Repairing":
                raise MechanicActionConflict("Only requests in repair can be marked complete.")
            service_request.status = "Done"
            service_request.estimated_completion_date = timezone.now()
            update_fields.append("estimated_completion_date")
            action_text = "marked complete"
            driver_text = "The mechanic marked the service work complete."
        else:
            raise ValueError(f"Unsupported mechanic request action: {action}")

        service_request.save(update_fields=update_fields)
        MechanicNotification.objects.create(
            mechanic=locked_mechanic,
            message=f"You {action_text} service request #{service_request.pk}.",
        )
        DriverNotification.objects.create(
            driver=service_request.driver,
            message=driver_text,
        )
        transaction.on_commit(
            partial(dispatch_mechanic_action_notifications, service_request.pk, action)
        )

    return service_request


class ManagerClaimConflict(Exception):
    def __init__(self, detail, code="claim_failed", status_code=409):
        self.detail = detail
        self.code = code
        self.status_code = status_code
        super().__init__(detail)


def claim_and_assign_request(*, manager, request_id, mechanic_id):
    with transaction.atomic():
        locked_manager = Manager.objects.select_for_update().get(pk=manager.pk)
        if not locked_manager.status or not locked_manager.is_email_verified:
            raise ManagerClaimConflict(
                "Your manager profile is not eligible to claim requests.",
                "manager_inactive",
                status_code=403,
            )

        manager_state = (locked_manager.state or "").strip()
        if not manager_state:
            raise ManagerClaimConflict(
                "Add a state to your manager profile before using the request queue.",
                "manager_state_missing",
                status_code=403,
            )

        service_request = Request.objects.select_for_update().select_related(
            "driver__user"
        ).get(
            pk=request_id,
            state__iexact=manager_state,
            status="Pending",
            manager__isnull=True,
            mechanic__isnull=True,
        )

        has_other_active = Request.objects.filter(
            manager=locked_manager,
            status__in=("Accepted", "Repairing", "Done"),
        ).exists()
        if has_other_active:
            raise ManagerClaimConflict(
                "Complete or release your active request before claiming another one.",
                "manager_busy",
            )

        locked_mechanic = Mechanic.objects.select_for_update().get(
            pk=mechanic_id,
            my_manager=locked_manager,
            status=True,
            is_email_verified=True,
        )

        has_other_active = Request.objects.filter(
            mechanic=locked_mechanic,
            status__in=("Accepted", "Repairing", "Done"),
        ).exists()
        if has_other_active:
            raise ManagerClaimConflict(
                "This mechanic already has an active request. Choose another mechanic.",
                "mechanic_busy",
            )

        service_request.status = "Accepted"
        service_request.manager = locked_manager
        service_request.mechanic = locked_mechanic
        service_request.save(update_fields=["status", "manager", "mechanic"])

        mechanic_name = locked_mechanic.get_name.strip() or f"Mechanic #{locked_mechanic.pk}"
        ManagerNotification.objects.create(
            manager=locked_manager,
            message=f"You accepted request #{service_request.pk} and assigned it to {mechanic_name}.",
        )
        MechanicNotification.objects.create(
            mechanic=locked_mechanic,
            message=f"Your manager assigned request #{service_request.pk} to you.",
        )
        DriverNotification.objects.create(
            driver=service_request.driver,
            message="Your service request has been accepted and assigned to a mechanic.",
        )
        transaction.on_commit(partial(dispatch_claim_notifications, service_request.pk))

    return service_request


def dispatch_claim_notifications(request_id):
    try:
        service_request = Request.objects.select_related(
            "driver__user", "manager__user", "mechanic__user"
        ).get(pk=request_id)
    except Request.DoesNotExist:
        logger.exception("Claimed request %s disappeared before notification dispatch", request_id)
        return

    driver_email = service_request.driver.user.email
    if driver_email:
        _run_optional_effect(
            request_id,
            "request claimed email",
            partial(
                send_html_email,
                subject=f"Request Accepted by {service_request.manager.user.first_name}",
                template_name="mails/request_accepted.html",
                context={"user": service_request.driver.user, "request": service_request},
                recipient_list=[driver_email],
            ),
        )


def dispatch_mechanic_action_notifications(request_id, action):
    try:
        service_request = Request.objects.select_related("driver__user", "mechanic__user").get(
            pk=request_id
        )
    except Request.DoesNotExist:
        logger.exception("Updated request %s disappeared before notification dispatch", request_id)
        return

    driver_email = service_request.driver.user.email
    if action == "accept" and driver_email:
        _run_optional_effect(
            request_id,
            "request accepted email",
            partial(
                send_html_email,
                subject=f"Request Accepted by {service_request.mechanic.user.first_name}",
                template_name="mails/request_accepted.html",
                context={"user": service_request.driver.user, "request": service_request},
                recipient_list=[driver_email],
            ),
        )
