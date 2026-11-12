# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Request, Mechanic
from .utils import send_html_email

@receiver(post_save, sender=Request)
def handle_request_notifications(sender, instance, created, **kwargs):
    """
    Notify relevant users when a request is created or approved.
    """
    if created:  # Notify all mechanics about a new request
        notify_mechanics_about_request(instance)

    elif instance.status == 'Approved':  # Notify the driver when the request is approved
        notify_driver_about_approval(instance)


def notify_mechanics_about_request(request):
    """
    Notify all mechanics about a new request.
    """
    mechanics = Mechanic.objects.all()
    recipient_list = [mechanic.user.email for mechanic in mechanics if mechanic.user.email]

    send_html_email(
        subject="New Request Posted",
        template_name="mails/new_request.html",
        context={
            "request": request,
            "driver": request.driver,
        },
        recipient_list=recipient_list,
    )


def notify_driver_about_approval(request):
    """
    Notify the driver about their request approval.
    """
    send_html_email(
        subject="Your Request Has Been Approved",
        template_name="mails/request_approved.html",
        context={
            "user": request.driver.user,
            "request": request,
        },
        recipient_list=[request.driver.user.email],
    )
    mechanics = Mechanic.objects.all()
    recipient_list = [mechanic.user.email for mechanic in mechanics if mechanic.user.email]

    send_html_email(
        subject="Request Approved",
        template_name="mails/mechanic_request_approved.html",
        context={
            "request": request,
            "driver": request.driver,
        },
        recipient_list=recipient_list,
        )