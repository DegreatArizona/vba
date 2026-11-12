# utils.py
import requests
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.signing import Signer, BadSignature
from datetime import date, timedelta
from .models import Driver, Mechanic, Manager

def remove_expired_pro_subscriptions():
    """
    Deactivate Pro status for Drivers, Mechanics, and Managers whose subscriptions have expired.
    """
    # For Drivers
    expired_drivers = Driver.objects.filter(
        is_pro=True, subscription_expiration_date__lt=date.today()
    )
    for driver in expired_drivers:
        driver.is_pro = False
        driver.save()
        print(f"Removed Pro status for Driver: {driver.get_name}")

    # For Mechanics
    expired_mechanics = Mechanic.objects.filter(
        is_pro=True, subscription_expiration_date__lt=date.today()
    )
    for mechanic in expired_mechanics:
        mechanic.is_pro = False
        mechanic.save()
        print(f"Removed Pro status for Mechanic: {mechanic.get_name}")

    # For Managers
    expired_managers = Manager.objects.filter(
        is_pro=True, subscription_expiration_date__lt=date.today()
    )
    for manager in expired_managers:
        manager.is_pro = False
        manager.save()
        print(f"Removed Pro status for Manager: {manager.get_name}")





signer = Signer()

def generate_token(email):
    """Generates a secure token for email."""
    return signer.sign(email)

def verify_token(token):
    """Verifies and extracts the email from the token."""
    try:
        email = signer.unsign(token)
        return email
    except BadSignature:
        return None



def send_html_email(subject, template_name, context, recipient_list):
    """
    Send an email with an HTML template.
    """
    html_content = render_to_string(template_name, context)
    email = EmailMultiAlternatives(
        subject=subject,
        body='',  # Optional plain text message (if needed)
        from_email=settings.EMAIL_HOST_USER,
        to=recipient_list,
    )
    email.attach_alternative(html_content, "text/html")
    email.send()


def send_email(subject, message, recipient_list):
    """
    Send an email.
    """
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        recipient_list,
        fail_silently=False,
    )


def safe_send_email(subject, html_content, recipient_list):
    """
    Sends an email with HTML content to a list of recipients.
    """
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body='',  # Optional plain text
            from_email=settings.EMAIL_HOST_USER,
            to=recipient_list,
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
    except Exception as e:
        print(f"Failed to send email to {recipient_list}: {e}")



def verify_account(account_number, bank_code):
    """
    Function to verify a customer's account number and bank code using Korapay's API.
    """
    url = f"{settings.KORAPAY_BASE_URL}/merchant/api/v1/misc/verify-account"
    headers = {
        "Authorization": f"Bearer {settings.KORAPAY_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "account_number": account_number,
        "bank_code": bank_code,
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        if response.status_code == 200 and response_data.get("status") == "success":
            return {
                "status": True,
                "data": response_data.get("data"),
                "message": response_data.get("message"),
            }
        return {
            "status": False,
            "message": response_data.get("message", "Verification failed"),
        }
    except Exception as e:
        return {"status": False, "message": str(e)}
