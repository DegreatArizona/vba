from django.shortcuts import render, redirect, reverse, get_object_or_404
from . import models, forms
from django.db.models import Sum, Q
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout, authenticate, login
from django.contrib import messages
from django.conf import settings
from .models import  Driver, DriverNotification, Request, MechanicNotification, MechanicWithdrawalHistory, Mechanic, Manager, ManagerNotification, DriverFundHistory, ManagerWithdrawalHistory, User
from .forms import RequestForm, MechanicUpdateStatusForm, MechanicAcceptStatusForm, ServiceFrom, ManagerUserForm, ManagerForm
import logging
from django.utils import timezone
from datetime import datetime
import openai
import requests
import json
import os
from notix.notix_api import Notix
from functools import wraps
import hmac
import hashlib
import time
import calendar
from Crypto.Cipher import AES
from Crypto import Random
import base64
from binascii import hexlify as hexa
from django.http import JsonResponse
from .onesignal_service import send_notification
from .utils import send_html_email, generate_token, verify_token
from .request_services import RequestCreationConflict, create_driver_request
from django.contrib.auth.hashers import make_password
from .decorators import email_verified_required, request_assigned_to_user
from django.utils.timezone import localtime
from django.db.models.functions import TruncMonth


logger = logging.getLogger(__name__)

def is_driver(user):
    return user.groups.filter(name='DRIVER').exists()
def is_mechanic(user):
    return user.groups.filter(name='MECHANIC').exists()
def is_manager(user):
    return user.groups.filter(name='MANAGER').exists()



def apply_percentage_discount(original_value, percentage):
    if percentage < 0 or percentage > 100:
        raise ValueError("Percentage must be between 0 and 100")
    discount = original_value * (percentage / 100)
    return original_value - discount


# @csrf_exempt
# def korapay_webhook(request, request_id):
#     if request.method != 'POST':
#         return JsonResponse({"error": "Invalid request method"}, status=405)
#     try:
#         payload = json.loads(request.body)
#         data = payload.get("data")
#         korapay_signature = request.headers.get("x-korapay-signature")
#         # Retrieve your Korapay secret key
#         korapay_secret_key = settings.KORAPAY_TEST_SECRET_KEY
#         # Compute the signature
#         computed_signature = hmac.new(
#             bytes(korapay_secret_key, 'utf-8'),
#             json.dumps(data, separators=(',', ':')).encode('utf-8'),
#             hashlib.sha256
#         ).hexdigest()
#         # Verify signature
#         if korapay_signature != computed_signature:
#             return JsonResponse({"error": "Invalid signature"}, status=400)
#         transaction = get_object_or_404(Request, pk=request_id)
#         # Process the transaction
#         event_type = payload.get("event")
#         transaction_status = data.get("status")
#         if event_type == "charge.success" and transaction_status == "success":
#             if not transaction.mechanic:
#                 return JsonResponse({"error": "No mechanic assigned to this transaction"}, status=400)
#             logger.info(f"Mechanic before update: {transaction.mechanic}")
#             logger.info(f"Salary before update: {transaction.mechanic.salary}")
#             transaction.mechanic.salary = (transaction.mechanic.salary or 0) + transaction.cost
#             transaction.mechanic.save()
#             transaction.transaction_reference = data.get("reference")
#             transaction.currency = data.get("currency")
#             transaction.invoice = 'Paid'
#             transaction.method = 'Card'
#             transaction.status = 'Released'
#             transaction.save()
#             notify = MechanicNotification(
#                 mechanic=transaction.mechanic,
#                 message=f"Payment Recieved from {transaction.driver.user.first_name}"
#             )
#             notify.save()
#             send_html_email(
#             subject=f"Payment Recieved from {transaction.driver.user.first_name}",
#             template_name="mails/payment.html",
#             context={"user": transaction.mechanic.user, "request": transaction},
#             recipient_list=[transaction.mechanic.user.email],
#             )
#             logger.info(f"Salary after update: {transaction.mechanic.salary}")
#             return JsonResponse({"status": "success", "message": "Transaction processed"}, status=200)
#         logger.info(data)
#         logger.info(transaction)
#         print(data)
#         print(transaction)
#         return JsonResponse({"status": "ignored", "message": "Event not handled"}, status=200)
#     except Exception as e:
#         logger.error("Error processing webhook: %s", str(e))
#         return JsonResponse({"error": str(e)}, status=500)



@csrf_exempt
def create_virtual_account(driver):
    """
    Create a virtual bank account for a new driver.
    This method is called after a driver is registered.
    try:
                            create_virtual_account(driver)
                        except Exception as e:
                            messages.warning(request, f"Virtual account creation failed: {str(e)}")

                        # After creating the driver, create the virtual account for them
                        return create_virtual_account(driver)
    """
    try:
        # Define the API URL to create a virtual bank account
        url = "https://api.korapay.com/merchant/api/v1/virtual-bank-account"
        
        # Prepare the payload to create the virtual bank account
        payload = {
            "account_name": f"{driver.user.first_name} {driver.user.last_name}",  # Driver's full name
            "account_reference": f"driver-{driver.id}",  # Reference for the account
            "permanent": True,  # Permanent account for the driver
            "bank_code": "000",  # Bank code for the bank you are integrating (e.g., Wema Bank)
            "customer": {
                "name": f"{driver.user.first_name} {driver.user.last_name}",
                "email": driver.user.email,
            }
        }

        # Define headers, including your API token
        headers = {
            "Authorization": f"Bearer {settings.KORAPAY_TEST_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        # Make the POST request to Korapay API to create the virtual account
        response = requests.post(url, json=payload, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()

            # Save the virtual account number and bank name into the driver's record
            driver.virtual_account_number = data['data']['account_number']
            driver.bank_name = data['data']['bank_name']  # Save the bank name from the response
            driver.save()

            return JsonResponse({
                "status": "success",
                "message": "Virtual bank account created successfully",
                "account_number": data['data']['account_number'],
                "bank_name": data['data']['bank_name']
            })

        else:
            return JsonResponse({
                "status": "error",
                "message": f"Error: {response.text}"
            }, status=response.status_code)

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }, status=500)


@csrf_exempt
def fund_virtual_account(request, driver_id, amount):
    try:
        # Get the driver's virtual account number
        driver = get_object_or_404(Driver, id=driver_id)

        # Ensure the driver has a valid virtual account number
        if not driver.virtual_account_number:
            return JsonResponse({
                "status": "error",
                "message": "Driver does not have a virtual account"
            }, status=400)

        # Define the API URL for crediting the virtual bank account
        url = "https://api.korapay.com/merchant/api/v1/virtual-bank-account/sandbox/credit"

        # Prepare the payload with the virtual account details and the amount to be credited
        payload = {
            "account_number": driver.virtual_account_number,  # Virtual account number
            "amount": amount,  # Amount to fund the account with
            "currency": "NGN"  # Currency (Naira in this case)
        }

        # Define the authorization headers with your Korapay API token
        headers = {
            "Authorization": f"Bearer {settings.KORAPAY_API_TOKEN}",  # Your Korapay API Token
            "Content-Type": "application/json"
        }

        # Send the request to Korapay API to credit the virtual account
        response = requests.post(url, json=payload, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            # Log or update the system based on the response
            return JsonResponse({
                "status": "success",
                "message": "Virtual bank account credited successfully",
                "data": data.get('data')
            })
        else:
            return JsonResponse({
                "status": "error",
                "message": f"Error: {response.text}"
            }, status=response.status_code)

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }, status=500)

def managers(request):
    return render(request, 'managers.html')

def mechanic_managers(request):
    # Fetch all managers
    managers = Manager.objects.all()
    
    # Create a list of manager data
    manager_list = [
        {
            "name": f"{manager.user.first_name} {manager.user.last_name}",
            "phone": manager.mobile,
        }
        for manager in managers
    ]
    
    return JsonResponse(manager_list, safe=False)

@csrf_exempt
def korapay_webhook(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        # Parse JSON payload
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON payload"}, status=400)

        data = payload.get("data", {})
        korapay_signature = request.headers.get("x-korapay-signature")
        korapay_secret_key = settings.KORAPAY_TEST_SECRET_KEY

        # Compute HMAC signature
        computed_signature = hmac.new(
            bytes(korapay_secret_key, 'utf-8'),
            json.dumps(data, separators=(',', ':')).encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if korapay_signature != computed_signature:
            return JsonResponse({"error": "Invalid signature"}, status=400)

        transaction_reference = data.get("reference")
        if not transaction_reference:
            return JsonResponse({"error": "Transaction reference missing"}, status=400)

        # Fetch transaction details
        korapay_url = f"https://api.korapay.com/merchant/api/v1/charges/{transaction_reference}"
        headers = {'Authorization': f'Bearer {korapay_secret_key}'}

        response = requests.get(korapay_url, headers=headers)
        if response.status_code != 200:
            return JsonResponse({"error": "Failed to fetch transaction details"}, status=400)

        response_data = response.json()
        transaction_metadata = response_data.get("data", {}).get("metadata", {})
        transaction_type = transaction_metadata.get("transaction_type")
        reference_id = transaction_metadata.get("reference_id")
        user = transaction_metadata.get("user")

        if not transaction_type and not user or not reference_id:
            return JsonResponse({"error": "Invalid transaction metadata"}, status=422)

        # Helper function for percentage calculation
        # def calculate_discount(value, percentage):
        #     if not 0 <= percentage <= 100:
        #         raise ValueError("Percentage must be between 0 and 100")
        #     return value * (percentage / 100)

        def apply_percentage_discount(original_value, percentage):
            if percentage < 0 or percentage > 100:
                raise ValueError("Percentage must be between 0 and 100")
            discount = original_value * (percentage / 100)
            return original_value - discount

        # Process "request_payment" type
        if data.get("status") == "success" and transaction_type == "request_payment":
            transaction = get_object_or_404(Request, pk=reference_id)
            if not transaction.mechanic:
                return JsonResponse({"error": "No mechanic assigned"}, status=400)

            company_charge = apply_percentage_discount(transaction.cost, 10)
            manager_charge = apply_percentage_discount(company_charge, 95) if transaction.manager else 0
            mechanic_charge = company_charge - manager_charge

            # Update salaries
            if transaction.manager:
                transaction.manager.salary = (transaction.manager.salary or 0) + manager_charge
                transaction.manager.save()

            transaction.mechanic.salary = (transaction.mechanic.salary or 0) + mechanic_charge
            transaction.mechanic.save()

            # Update transaction details
            transaction.transaction_reference = transaction_reference
            transaction.invoice = 'Paid'
            transaction.method = 'Card'
            transaction.status = 'Released'
            transaction.save()

            MechanicNotification.objects.create(
                mechanic=transaction.mechanic,
                message=f"Payment received from {transaction.driver.user.first_name}"
            )

            send_html_email(
                subject=f"Payment received from {transaction.driver.user.first_name}",
                template_name="mails/payment.html",
                context={"user": transaction.mechanic.user, "request": transaction},
                recipient_list=[transaction.mechanic.user.email],
            )
            return JsonResponse({"status": "success", "message": "Request payment processed"}, status=200)

        # Process "fund_wallet" type
        elif data.get("status") == "success" and transaction_type == "fund_wallet":
            driver = get_object_or_404(Driver, pk=reference_id)
            amount_received = data.get("amount", 0) - 50
            driver.balance += float(amount_received)
            driver.save()

            DriverFundHistory.objects.create(
                narration=data.get("narration", "Wallet Funding"),
                driver=driver,
                transaction_reference=data.get("reference"),
                currency="NGN",
                amount_recieved=amount_received,
                charges="50",
                status="Success"
            )
            DriverNotification.objects.create(
                driver=driver,
                message=f"Your account has been funded with ₦{amount_received}!"
            )

            send_html_email(
                subject=f"₦{amount_received} funded successfully",
                template_name="mails/fund.html",
                context={"user": driver.user, "amount": amount_received},
                recipient_list=[driver.user.email],
            )
            return JsonResponse({"status": "success", "message": "Wallet funded successfully"}, status=200)

        # Process "Subscription" type
        elif data.get("status") == "success" and transaction_type == "subscribe":
            if user == "driver":
                driver = get_object_or_404(Driver, pk=reference_id)
                driver.is_pro = True
                driver.save()
                DriverNotification.objects.create(
                    driver=driver,
                    message=f"Congratulations you have successfuly subscribe to our pro plan!"
                )
                msg1 = "Congratulations you have successfuly subscribe to our pro plan"
                msg2 = "Click the link below to login to your account and enjoy advanced features:"
                send_html_email(
                    subject="Congratulations Pro User",
                    template_name="mails/subscribe.html",
                    context={"user": driver.user, "message1": msg1, "message2":msg2},
                    recipient_list=[driver.user.email],
                )

            elif user == "mechanic":
                mechanic = get_object_or_404(Mechanic, pk=reference_id)
                mechanic.is_pro = True
                mechanic.save()
                MechanicNotification.objects.create(
                    mechanic=mechanic,
                    message=f"Congratulations you have successfuly subscribe to our pro plan!"
                )
                msg1 = "Congratulations you have successfuly subscribe to our pro plan"
                msg2 = "Click the link below to login to your account and enjoy advanced features:"
                send_html_email(
                    subject="Congratulations Pro User",
                    template_name="mails/subscribe.html",
                    context={"user": mechanic.user, "message1": msg1, "message2":msg2},
                    recipient_list=[mechanic.user.email],
                )

            elif user == "manager":
                manager = get_object_or_404(Manager, pk=reference_id)
                manager.is_pro = True
                manager.save()
                ManagerNotification.objects.create(
                    manager=manager,
                    message=f"Congratulations you have successfuly subscribe to our pro plan!"
                )
                msg1 = "Congratulations you have successfuly subscribe to our pro plan"
                msg2 = "Click the link below to login to your account and enjoy advanced features:"
                send_html_email(
                    subject="Congratulations Pro User",
                    template_name="mails/subscribe.html",
                    context={"user": manager.user, "message1": msg1, "message2":msg2},
                    recipient_list=[manager.user.email],
                )
            return JsonResponse({"status": "success", "message": "Wallet funded successfully"}, status=200)

        return JsonResponse({"status": "ignored", "message": "Unhandled event type"}, status=200)

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)


# @csrf_exempt
# def korapay_webhook(request):
#     if request.method != 'POST':
#         return JsonResponse({"error": "Invalid request method"}, status=405)

#     try:
#         payload = json.loads(request.body)
#         data = payload.get("data")
#         korapay_signature = request.headers.get("x-korapay-signature")

#         # Retrieve Korapay secret key
#         korapay_secret_key = settings.KORAPAY_TEST_SECRET_KEY

#         # Compute the signature
#         computed_signature = hmac.new(
#             bytes(korapay_secret_key, 'utf-8'),
#             json.dumps(data, separators=(',', ':')).encode('utf-8'),
#             hashlib.sha256
#         ).hexdigest()

#         # Verify signature
#         if korapay_signature != computed_signature:
#             return JsonResponse({"error": "Invalid signature"}, status=400)

#         # Get metadata to identify transaction purpose
#         metadata = data.get("metadata", {})
#         transaction_type = metadata.get("transaction_type")
#         reference_id = metadata.get("reference_id")

#         # Log metadata for debugging
#         logger.debug(f"Metadata received: {metadata}")

#         # Validate metadata
#         if not transaction_type or not reference_id:
#             logger.error("Invalid or missing transaction type or reference ID in metadata")
#             return JsonResponse({"error": "Invalid metadata: missing transaction type or reference ID"}, status=400)

#         # Process transaction based on type
#         if event_type == "charge.success" and transaction_status == "success":
#             # Handle wallet funding
#             if transaction_type == "wallet_funding":
#                 driver = get_object_or_404(Driver, pk=reference_id)
#                 driver.wallet_balance += data.get("amount", 0)
#                 driver.save()
#                 return JsonResponse({"status": "success", "message": "Wallet funded successfully"}, status=200)

#             # Handle subscription payments
#             elif transaction_type == "subscription":
#                 driver = get_object_or_404(Driver, pk=reference_id)
#                 driver.subscription_status = "Active"
#                 driver.subscription_expiry = timezone.now() + timedelta(days=30)
#                 driver.save()
#                 return JsonResponse({"status": "success", "message": "Subscription activated"}, status=200)

#             # Handle request payments
#             elif transaction_type == "request_payment":
#                 transaction = get_object_or_404(Request, pk=reference_id)
#                 if not transaction.mechanic:
#                     return JsonResponse({"error": "No mechanic assigned to this transaction"}, status=400)

#                 transaction.mechanic.salary = (transaction.mechanic.salary or 0) + transaction.cost
#                 transaction.mechanic.save()
#                 transaction.transaction_reference = data.get("reference")
#                 transaction.invoice = 'Paid'
#                 transaction.method = 'Card'
#                 transaction.status = 'Released'
#                 transaction.save()

#                 # Notify the mechanic
#                 MechanicNotification.objects.create(
#                     mechanic=transaction.mechanic,
#                     message=f"Payment received from {transaction.driver.user.first_name}"
#                 )

#                 send_html_email(
#                     subject=f"Payment received from {transaction.driver.user.first_name}",
#                     template_name="mails/payment.html",
#                     context={"user": transaction.mechanic.user, "request": transaction},
#                     recipient_list=[transaction.mechanic.user.email],
#                 )
#                 return JsonResponse({"status": "success", "message": "Request payment processed"}, status=200)

#         return JsonResponse({"status": "ignored", "message": "Event not handled"}, status=200)

#     except Exception as e:
#         logger.error("Error processing webhook: %s", str(e))
#         return JsonResponse({"error": str(e)}, status=500)


openai.api_key = settings.OPENAI_API_KEY
def get_completion(prompt):
    try:
        query = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # updated model name
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            n=1,
            temperature=0.5,
        )
        response = query.choices[0].message['content'].strip()
        return response
    except Exception as e:
        return f"Error: {str(e)}"

def query_view(request):
    if request.method == 'POST':
        prompt = request.POST.get('prompt')
        if prompt:
            try:
                response = get_completion(prompt)
                return JsonResponse({'response': response})
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'error': 'No prompt provided'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required(login_url='login')
def goPro(request):
    cost = 14000
    content = ['Featured listing for your mechanic services', 'Advanced analytics and reporting', 'Priority access to high-value breakdowns']
    return render(request, "pro.html", {"cost":cost, "content":content})
    

def reset_password(request, token):
    email = verify_token(token)
    if email:
        if request.method == 'POST':
            new_password = request.POST.get('password')
            try:
                user = User.objects.get(email=email)
                user.password = make_password(new_password)
                user.save()
                messages.success(request, "Password reset successfully!")
                return redirect('login')
            except User.DoesNotExist:
                messages.success(request, "User does not exist.")
                return redirect('register')
        return render(request, 'reset-password.html')
    messages.success(request, "Invalid or expired token.")
    return redirect('forgot-password')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            token = generate_token(email)
            reset_link = f"{settings.SITE_URL}/reset-password/{token}"
            msg1 = "Reset Your Password"
            msg2 = "Click the link below to reset your password:"
            send_html_email(
                subject="Welcome to Auto Aid",
                template_name="mails/verify.html",
                context={"user": user, "message1":msg1, "message2":msg2, "link":reset_link},
                recipient_list=[user.email],
            )
            print(f"Link: {reset_link} \nUser: {user}")
            messages.success(request, "Password reset email sent.")
            return redirect('forgot-password')
        except User.DoesNotExist:
            messages.success(request, "No user found with this email.")
            return redirect('register')
    return render(request, 'forgot-password.html')


# def verify_email(request, token):
#     email = verify_token(token)
#     if email:
#         try:
#             user = User.objects.get(email=email)
#             user.is_email_verified = True
#             user.is_active = True
#             user.save()
#             return HttpResponse("Email verified successfully!")
#         except User.DoesNotExist:
#             return HttpResponse("User does not exist.")
#     return HttpResponse("Invalid or expired token.")


def verify_email(request, token):
    # Decode the email from the token
    email = verify_token(token)
    if email:
        try:
            # Check if the user exists
            user = User.objects.get(email=email)

            # Determine the role and verify email
            if Driver.objects.filter(user=user).exists():
                driver = Driver.objects.get(user=user)
                driver.is_email_verified = True
                driver.is_active = True
                driver.save()
                send_html_email(
                    subject="Welcome to Auto Aid",
                    template_name="mails/driver_welcome.html",
                    context={"user": user},
                    recipient_list=[user.email],
                )
                messages.success(request, "Driver email verified successfully!")
                return HttpResponseRedirect(reverse('driver-dashboard'))
                

            elif Manager.objects.filter(user=user).exists():
                manager = Manager.objects.get(user=user)
                manager.is_email_verified = True
                manager.is_active = True
                manager.save()
                send_html_email(
                    subject="Welcome to Auto Aid",
                    template_name="mails/mechanic_welcome.html",
                    context={"user": user},
                    recipient_list=[user.email],
                )
                messages.success(request, "Manager email verified successfully!")
                return HttpResponseRedirect(reverse('manager-dashboard'))
                

            elif Mechanic.objects.filter(user=user).exists():
                mechanic = Mechanic.objects.get(user=user)
                mechanic.is_email_verified = True
                mechanic.is_active = True
                mechanic.save()
                send_html_email(
                    subject="Welcome to Auto Aid",
                    template_name="mails/mechanic_welcome.html",
                    context={"user": user},
                    recipient_list=[user.email],
                )
                messages.success(request, "Mechanic email verified successfully!")
                return HttpResponseRedirect(reverse('mechanic-dashboard'))
                
                messages.success(request, "User role not found.")
            return HttpResponseRedirect(reverse('register'))
            
        except User.DoesNotExist:
            messages.success(request, "User does not exist.")
            return HttpResponseRedirect(reverse('register', ))
    messages.success(request, "Invalid or expired token.")
    return render(request, "registration_pending.html")
    



def resend_verification_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = get_object_or_404(User, email=email)
            
            driver = Driver.objects.filter(is_email_verified=True)
            manager = Manager.objects.filter(is_email_verified=True)
            mechanic = Mechanic.objects.filter(is_email_verified=True)
            if request.user.is_authenticated and (
                (driver == request.user) or
                (manager == request.user) or
                (mechanic == request.user) 
            ):
                messages.info(request, "Your email is already verified.")
                return redirect('login') 
            token = generate_token(email)
            verification_link = f"{settings.SITE_URL}/verify-email/{token}"
            msg1 = "Resend Email Verification"
            msg2 = "Click the link below to verify your email:"
            send_html_email(
                subject="Resend Email Verification",
                template_name="mails/verify.html",
                context={"user": user, "message1":msg1, "message2":msg2, "link":verification_link},
                recipient_list=[user.email],
            )
            
            messages.success(request, "Verification email resent. Please check your inbox.")
        except User.DoesNotExist:
            messages.warning(request, "No user found with this email.")
            return redirect('register')
    return HttpResponseRedirect(reverse('login'))
    
    

def index(request):
    return render(request, 'index.html')

def register(request):
    if request.method == 'POST':
        if 'mechanic_submit' in request.POST:
            userForm = forms.MechanicUserForm(request.POST)
            serviceForm = forms.ServiceFrom(request.POST)
            mechanicForm = forms.MechanicForm(request.POST, request.FILES)
            password1 = request.POST['password']
            password2 = request.POST['rPassword']
            if password1 == password2:
                if userForm.is_valid() and mechanicForm.is_valid() and serviceForm.is_valid():
                    try:
                        user = userForm.save()
                        user.set_password(user.password)
                        user.save()
                        mechanic = mechanicForm.save(commit=False)
                        mechanic.user = user
                        selected_services = [key for key, value in serviceForm.cleaned_data.items() if value]
                        mechanic.service = ', '.join(selected_services)
                        mechanic.save()
                        mechanic_group, created = Group.objects.get_or_create(name='MECHANIC')
                        mechanic_group.user_set.add(user)
                        messages.success(request, "Your account have been created successfully.")
                        msg1 = "Verify Your Email"
                        msg2 = "Click the link below to verify your email:"
                        token = generate_token(user.email)
                        verification_link = f"{settings.SITE_URL}/verify-email/{token}"
                        send_html_email(
                            subject="Welcome to Auto Aid",
                            template_name="mails/verify.html",
                            context={"user": user, "message1":msg1, "message2":msg2, "link":verification_link},
                            recipient_list=[user.email],
                        )
                        
                        send_html_email(
                            subject="New registered user",
                            template_name="mails/new_user.html",
                            context={"user": user},
                            recipient_list=[settings.EMAIL_HOST_NAME],
                        )
                        return render(request, 'registration_pending.html', {'current_year': datetime.now().year})
                    except Exception as e:
                        messages.warning(request, f"Error while creating account. Please contact support. Details: {e}")
                        return HttpResponseRedirect(reverse('register'))
                else:
                    messages.warning(request, "Invalid form data: Username or Email address is taken!")
                    return HttpResponseRedirect(reverse('register'))
            else:
                messages.warning(request, "Password mismatch. Please confirm the password.")
                return HttpResponseRedirect(reverse('register'))
            

        elif 'driver_submit' in request.POST:
            userForm = forms.DriverUserForm(request.POST)
            driverForm = forms.DriverForm(request.POST)
            password1 = request.POST['password']
            password2 = request.POST['rPassword']
            if password1 == password2:
                if userForm.is_valid() and driverForm.is_valid():
                    try:
                        user = userForm.save()
                        user.set_password(user.password)
                        user.save()
                        driver = driverForm.save(commit=False)
                        driver.user = user
                        driver.save()
                        driver_group, _ = Group.objects.get_or_create(name='DRIVER')
                        driver_group.user_set.add(user)
                        messages.success(request, "Your account have been created successfully, you can now procced to login")

                        msg1 = "Verify Your Email"
                        msg2 = "Click the link below to verify your email:"
                        token = generate_token(user.email)
                        verification_link = f"{settings.SITE_URL}/verify-email/{token}"
                        send_html_email(
                            subject="Welcome to Auto Aid",
                            template_name="mails/verify.html",
                            context={"user": user, "message1":msg1, "message2":msg2, "link":verification_link},
                            recipient_list=[user.email],
                        )

                        send_html_email(
                            subject="New registered user",
                            template_name="mails/new_user.html",
                            context={"user": user},
                            recipient_list=[settings.EMAIL_HOST_NAME],
                        )
                        return render(request, 'registration_pending.html', {'current_year': datetime.now().year})
                    except Exception as e:
                        messages.warning(request, f"Error while creating account. Please contact support. Details: {e}")
                        return HttpResponseRedirect(reverse('register'))
                else:
                    messages.warning(request, "Invalid form data: Username or Email address is taken!")
                    return HttpResponseRedirect(reverse('register'))
            else:
                messages.warning(request, "Password mismatch. Please confirm the password.")
                return HttpResponseRedirect(reverse('register'))
    serviceForm = forms.ServiceFrom()
    return render(request, 'register.html', {'serviceForm':serviceForm})


def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))
    

#for checking user driver, mechanic or admin(by sumit)

def loginUser(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            try:
                if is_driver(user):
                    messages.success(request, "Driver logged in successfully!")
                    return HttpResponseRedirect(reverse('driver-dashboard'))
                elif is_mechanic(user):
                    account_approved = models.Mechanic.objects.filter(user_id=user.id, status=True).exists()
                    if account_approved:
                        messages.success(request, "Mechanic logged in successfully!")
                        return HttpResponseRedirect(reverse('mechanic-dashboard'))
                    else:
                        messages.warning(request, "Your account is pending approval.")
                        return HttpResponseRedirect(reverse('afterlogin'))
                elif is_manager(user):
                    account_approved = models.Manager.objects.filter(user_id=user.id, status=True).exists()
                    if account_approved:
                        messages.success(request, "Manager logged in successfully!")
                        return HttpResponseRedirect(reverse('manager-dashboard'))
                    else:
                        messages.warning(request, "Your account is pending approval.")
                        return HttpResponseRedirect(reverse('afterlogin'))
                else:
                    messages.warning(request, "Invalid login credentials. Please confirm your username or password and try again. \n or create a new account")
                    return HttpResponseRedirect(reverse('login'))
            except Exception as e:
                logger.warning(f"Login error for user {user.id}: {e}")
                messages.error(request, f"An error occurred during login. Please try again. Detail: {e}")
                return HttpResponseRedirect(reverse('login'))
        else:
            messages.warning(request, "Invalid username or password. Please try again.")
            return HttpResponseRedirect(reverse('login'))
    return render(request, 'login.html')

@csrf_exempt
@login_required(login_url='login')
@user_passes_test(is_mechanic)
@request_assigned_to_user
def update_mechanic_location(request, request_id):
    if request.method == 'POST':
        try:
            mechanic = models.Mechanic.objects.get(user_id=request.user.id)
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            if not (latitude and longitude):
                return JsonResponse({'error': 'Latitude and longitude are required'}, status=400)

            request_objs = models.Request.objects.filter(mechanic=mechanic, pk=request_id).select_related('driver')

            if not request_objs.exists():
                return JsonResponse({'error': 'No active requests found for mechanic'}, status=404)

            request_objs.update(latitude=latitude, longitude=longitude, mechanic=mechanic)

            return JsonResponse({'status': 'Locations updated', 'updated_count': request_objs.count()})
        except models.Mechanic.DoesNotExist:
            return JsonResponse({'error': 'Mechanic not found'}, status=404)
        except Exception as e:
            print(e)
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
@login_required(login_url='login')
@user_passes_test(is_driver)
@request_assigned_to_user
def get_mechanic_location(request, request_id):
    if request.method == 'GET':
        try:
            # Ensure the user is a driver
            driver = models.Driver.objects.get(user_id=request.user.id)
            # Fetch the latest mechanic location related to the driver
            request_obj = models.Request.objects.filter(driver=driver, pk=request_id).select_related('mechanic').order_by('-id').first()
            if not request_obj:
                print(request_obj)
                return JsonResponse({'error': 'No location data found'}, status=404)
            print(request_obj)
            return JsonResponse({
                'latitude': request_obj.latitude,
                'longitude': request_obj.longitude,
            })
        except models.Driver.DoesNotExist:
            return JsonResponse({'error': 'Driver not found'}, status=404)
        except Exception as e:
            print(e)
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)
    
##################################
#             Driver             #
##################################
@login_required(login_url='login')
@user_passes_test(is_driver)
@email_verified_required
def driverFund(request):
    driver=models.Driver.objects.get(user_id = request.user.id)
    history = models.DriverFundHistory.objects.filter(driver_id=driver.id).order_by('-date')
    timestamp = str(calendar.timegm(time.gmtime()))
    unique_string = f"{driver.id}{timestamp}"
    transaction_ref = f"TXN{driver.id}{hashlib.sha256(unique_string.encode()).hexdigest()[:10]}"
    return render(request, 'driver-fund-wallet.html', {'driver':driver, 'ref':transaction_ref, 'history':history})
    


@login_required(login_url='login')
@user_passes_test(is_driver)
@request_assigned_to_user
@email_verified_required
def driverTrack(request, request_id):
    driver=models.Driver.objects.get(user_id = request.user.id)
    accept = get_object_or_404(Request, pk=request_id)
    return render(request, 'driver-track-mechanic.html', {'accept':accept, 'driver':driver})

@login_required(login_url='login')
@user_passes_test(is_driver)
@email_verified_required
def driverDashboard(request):
    driver=models.Driver.objects.get(user_id = request.user.id)
    work_in_progress=models.Request.objects.all().filter(driver_id=driver.id).filter(Q(status="Accepted") | Q(status="Done") | Q(status="Repairing")).count()
    work_completed=models.Request.objects.all().filter(driver_id=driver.id).filter(Q(status="Released")).count()
    new_request_made=models.Request.objects.all().filter(driver_id=driver.id).filter(Q(status="Pending") | Q(status="Done") | Q(status="Approved")).count()
    bill=models.Request.objects.all().filter(driver_id=driver.id).filter(Q(status="Released")).aggregate(Sum('cost'))
    notifications = driver.notifications.all().order_by('-timestamp')
    requests = models.Request.objects.filter(driver_id=driver.id).select_related('mechanic').order_by('-date')
    active_requests = Request.objects.all().filter(driver=driver).exclude(status__in=['Cancelled', 'Released']).order_by('-date')
    accept_requests = models.Request.objects.filter(driver_id=driver.id).filter(status__in=['Accepted', 'Done', 'Repairing']).select_related('mechanic').order_by('-date')
    timestamp = str(calendar.timegm(time.gmtime()))
    unique_string = f"{driver.id}{timestamp}"
    transaction_ref = f"TXN{driver.id}{hashlib.sha256(unique_string.encode()).hexdigest()[:10]}"
    print(bill)
    dict={
    'work_in_progress':work_in_progress,
    'work_completed':work_completed,
    'new_request_made':new_request_made,
    'bill':bill['cost__sum'] or 0,
    'driver':driver,
    'notifications': notifications,
    'requests':requests,
    'active_requests': active_requests,
    'accept_requests':accept_requests,
    "ref":transaction_ref,
    }
    return render(request, 'driver-dashboard.html', context=dict)

@login_required(login_url='login')
@user_passes_test(is_driver)
@email_verified_required
def driverProfile(request):
    driver = models.Driver.objects.get(user_id=request.user.id)
    user = models.User.objects.get(id=driver.user_id)
    userForm = forms.DriverUserForm(instance=user)
    driverForm = forms.DriverForm(instance=driver)
    if request.method == 'POST':
        userForm = forms.DriverUserForm(request.POST, instance=user)
        driverForm = forms.DriverForm(request.POST, request.FILES, instance=driver)
        if userForm.is_valid() and driverForm.is_valid():
            try:
                user = userForm.save(commit=False)
                user.set_password(userForm.cleaned_data['password'])
                user.save()
                driverForm.save()
                messages.success(request, "Profile updated successfully.")
                notify = models.DriverNotification(
                    driver=request.user.driver,
                    message="Profile updated successfully."
                )
                notify.save()
                return HttpResponseRedirect(reverse('driver-profile'))
            except Exception as e:
                messages.warning(request, f"Error while editing profile. Please contact support. Details: {e}")
                return HttpResponseRedirect(reverse('driver-profile'))
        else:
            messages.warning(request, f"Invalid form data: {userForm.errors}, {driverForm.errors}")
            return HttpResponseRedirect(reverse('driver-profile'))
    return render(request, 'driver-profile.html', {'driver': driver, 'userForm': userForm, 'driverForm': driverForm})
    
@login_required(login_url='login')
@user_passes_test(is_driver)
@email_verified_required
def requestHistory(request):
    driver=models.Driver.objects.get(user_id = request.user.id)
    requests = models.Request.objects.filter(driver=driver).order_by('-date')
    dict = {
        'driver':driver,
        'requests': requests,
    }
    return render(request, 'driver-request-history.html', context=dict)

@login_required(login_url='login')
@user_passes_test(is_driver)
@email_verified_required
def requestService(request):
    driver = models.Driver.objects.get(user_id=request.user.id)
    if request.method == "POST":
        values = {
            "vehicle_no": request.POST.get("vehicle_no"),
            "vehicle_name": request.POST.get("vehicle_name"),
            "problem_description": request.POST.get("problem_description"),
            "category": request.POST.get("category"),
            "state": request.POST.get("state"),
            "location": request.POST.get("location"),
            "mobile": request.POST.get("mobile"),
        }
        try:
            create_driver_request(driver=driver, values=values)
        except RequestCreationConflict as conflict:
            messages.warning(request, conflict.detail)
            if conflict.code == "pending_invoice":
                return redirect("driver-invoice-history")
            return redirect("driver-dashboard")
        except Exception:
            logger.exception("Unable to create a driver service request")
            messages.warning(request, "We could not create your request. Please try again.")
            return redirect("driver-dashboard")

        messages.success(request, "Your request has been created and is awaiting admin approval.")
        return HttpResponseRedirect(reverse("driver-dashboard"))

    return render(request, "driver-request-service.html", {"driver": driver})

def notify_users(category, location):
    """
    Sends a notification to users via OneSignal.
    """
    message = f"A new service request for {category} at {location} has been created and awaiting admin approval."
    try:
        response = send_notification(message)
        print("Notification sent:", response.to_dict())
    except Exception as e:
        print(f"Notification error: {e}")

@login_required(login_url='login')
@user_passes_test(is_driver)
@email_verified_required
def driverNotification(request):
    driver = models.Driver.objects.get(user_id = request.user.id)
    notifications = driver.notifications.all().order_by('-timestamp')
    dict={
    'driver':driver,
    'notifications': notifications,
    }
    return render(request, 'driver-notification.html', context=dict)

@login_required(login_url='login')
@user_passes_test(is_driver)
@request_assigned_to_user
@email_verified_required
def requestDetail(request, request_id):
    driver = models.Driver.objects.get(user_id=request.user.id)
    request_detail = models.Request.objects.get(pk=request_id)
    return render(request, 'driver-request-detail.html', {'driver': driver, 'request': request_detail})
    
@login_required(login_url='login')
@user_passes_test(is_driver)
@request_assigned_to_user
@email_verified_required
def requestEdit(request, request_id):
    driver=models.Driver.objects.get(user_id = request.user.id)
    request_detail = get_object_or_404(Request, pk=request_id)  # Get the request instance
    if request.method == 'POST':
        form = RequestForm(request.POST, instance=request_detail)
        if form.is_valid():
            form.save()  # Save the updated request
            return HttpResponseRedirect('driver-request-detail', pk=request_detail.request_id)  # Redirect to the detail page
    else:
        form = RequestForm(instance=request_detail)  # Create a form instance with current data
    return render(request, 'driver-request-edit.html', {'form': form, 'driver':driver, 'request': request_detail})

@login_required(login_url='login')
@user_passes_test(is_driver)
@request_assigned_to_user
@email_verified_required
def requestDelete(request, request_id):
    driver=models.Driver.objects.get(user_id = request.user.id)
    request_detail = get_object_or_404(Request, pk=request_id)
    if request.method == 'POST':
        request_detail.delete()  # Delete the request
        notify = DriverNotification(
            driver=request.user.driver,
            message=f"You have success fully deleted your request with id {request_id}"
        )
        notify.save()  # Save the notification
        return redirect('driver-dashboard')  # Redirect after deletion
    return render(request, 'driver-request-delete.html', {'request': request_detail, 'driver':driver})

@login_required(login_url='login')
@user_passes_test(is_driver)
@request_assigned_to_user
@email_verified_required
def requestCancel(request, request_id):
    driver=models.Driver.objects.get(user_id = request.user.id)
    request_detail = get_object_or_404(Request, pk=request_id)
    if request.method == 'POST':
        request_detail.status = 'Cancelled'
        request_detail.invoice = 'Cancelled'
        request_detail.save()  

        notify = DriverNotification(
            driver=request.user.driver,
            message=f"You have successfully cancelled your request with ID: {request_id}"
        )
        notify.save()
        return redirect('driver-dashboard')  
    return render(request, 'driver-request-cancel.html', {'request': request_detail, 'driver':driver})


@login_required(login_url='login')
@user_passes_test(is_driver)
@email_verified_required
def invoiceHistory(request):
    driver = models.Driver.objects.get(user_id = request.user.id)
    invoices = models.Request.objects.all().filter(driver_id=driver.id)
    context={
        'driver':driver,
        'invoices':invoices
    }
    return render(request, 'driver-invoice-history.html', context)

@login_required(login_url='login')
@user_passes_test(is_driver)
@request_assigned_to_user
@email_verified_required
def driverInvoice(request, request_id):
    driver = models.Driver.objects.get(user_id=request.user.id)
    invoices = models.Request.objects.all().filter(driver_id=driver.id)
    invoice_detail = models.Request.objects.get(pk=request_id)
    total = (invoice_detail.cost or 0) + invoice_detail.tax
    timestamp = str(calendar.timegm(time.gmtime()))
    unique_string = f"{driver.id}{timestamp}"
    transaction_ref = f"TXN{driver.id}{hashlib.sha256(unique_string.encode()).hexdigest()[:10]}"
    if request.method == "POST":
        if not invoice_detail.mechanic:
            messages.warning(request, "No mechanic assigned")
        try:

            if float(driver.balance) >= float(invoice_detail.cost):
                driver.balance -= float(invoice_detail.cost)
                driver.save()
                company_charge = apply_percentage_discount(invoice_detail.cost, 10)
                manager_charge = apply_percentage_discount(company_charge, 95) if invoice_detail.manager else 0
                mechanic_charge = company_charge - manager_charge

                # Update salaries
                if invoice_detail.manager:
                    invoice_detail.manager.salary = (invoice_detail.manager.salary or 0) + manager_charge
                    invoice_detail.manager.save()

                invoice_detail.mechanic.salary = (invoice_detail.mechanic.salary or 0) + mechanic_charge
                invoice_detail.mechanic.save()

                # Update transaction details
                invoice_detail.transaction_reference = transaction_ref
                invoice_detail.invoice = 'Paid'
                invoice_detail.method = 'Balance'
                invoice_detail.status = 'Released'
                invoice_detail.save()

                MechanicNotification.objects.create(
                    mechanic=invoice_detail.mechanic,
                    message=f"Payment received from {invoice_detail.driver.user.first_name}"
                )

                send_html_email(
                    subject=f"Payment received from {invoice_detail.driver.user.first_name}",
                    template_name="mails/payment.html",
                    context={"user": invoice_detail.mechanic.user, "request": invoice_detail},
                    recipient_list=[invoice_detail.mechanic.user.email],
                )
            else:
                messages.warning(request, "Insufficient balance, please fund your wallet to procced with this transactio!")
                return HttpResponseRedirect(reverse('driver-fund-wallet', ))
                
        except Exception as e:
            print(f"An error occured Detail: {e}")
    return render(request, 'driver-invoice.html', {'driver': driver, 'request': invoice_detail, 'invoices':invoices,'ref':transaction_ref, 'total':total})
        
@login_required(login_url='login')
@user_passes_test(is_driver)
@email_verified_required
def proRequest(request):
    driver = models.Driver.objects.get(user_id=request.user.id)
    mechanics = models.Mechanic.objects.filter(is_pro=False)
    state = request.GET.get('state')
    local_government = request.GET.get('local_government')
    if state:
        mechanics = mechanics.filter(state=state)
    if local_government:
        mechanics = mechanics.filter(local_government=local_government)
    work_completed = {}
    for mechanic in mechanics:
        count = models.Request.objects.filter(
            mechanic_id=mechanic.id, status__iexact="Released"
        ).count()
        work_completed[mechanic.id] = count
        print(f"Mechanic ID: {mechanic.id}, Completed Jobs: {count}")  # Debugging

    work_in_progress = {}
    for mechanic in mechanics:
        count = models.Request.objects.filter(
            mechanic_id=mechanic.id,
        ).filter(Q(status="Accepted") | Q(status="Done") | Q(status="Repairing")).count()
        work_in_progress[mechanic.id] = count  # Fix here
        print(f"Mechanic ID: {mechanic.id}, In-progress Jobs: {count}")  # Debugging
    
    timestamp = str(calendar.timegm(time.gmtime()))
    unique_string = f"{driver.id}{timestamp}"
    transaction_ref = f"TXN{driver.id}{hashlib.sha256(unique_string.encode()).hexdigest()[:10]}"
    return render(request, 'driver-pro-request.html', {
        'mechanics': mechanics,
        'driver': driver,
        'work_completed': work_completed,
        'work_in_progress':work_in_progress,
        "ref":transaction_ref,
    })

@login_required(login_url='login')
@user_passes_test(is_driver)
@email_verified_required
def proRequestSend(request, mechanic_id):
    mechanic = get_object_or_404(models.Mechanic, id=mechanic_id, is_pro=False)
    if request.method == "POST":
        driver = get_object_or_404(models.Driver, user_id=request.user.id)
        existing_request = models.Request.objects.filter(
            driver=driver,
            mechanic=mechanic,
            status__in=['Pending', 'Done', 'Accepted', 'Approved'],
            invoice="Pending"
        ).exists()

        if existing_request:
            messages.warning(request, "You already have a pending or ongoing request or unpaid invoice with this mechanic.")
            return redirect('driver-pro-request') 
        
        new_request = models.Request.objects.create(
            vehicle_no=request.POST.get('vehicle_no'),
            vehicle_name=request.POST.get('vehicle_name'),
            problem_description=request.POST.get('problem_description'),
            category=request.POST.get('category'),
            location=request.POST.get('location'), 
            mobile=request.POST.get('mobile'), 
            driver=driver,
            mechanic=mechanic,
            status="Accepted", 
        )
        new_request.save()
        notify = DriverNotification(
            driver=request.user.driver,
            message=f"Request for {new_request.category} at {new_request.location} have been sent to {mechanic.user.first_name}."
        )
        notify.save()
        notify = MechanicNotification(
            mechanic=mechanic,
            message=f"{driver.user.first_name} just sent you a new request with id: {new_request.id} Problem {new_request.problem_description}"
        )
        notify.save()
        notify_users(new_request.category, new_request.location)
        send_html_email(
            subject="Request Posted Successfully",
            template_name="mails/request_posted.html",
            context={"user": driver.user, "request": new_request},
            recipient_list=[driver.user.email],
        )
        send_html_email(
            subject=f"New Request Recieved from {driver.user.first_name}",
            template_name="mails/new_request.html",
            context={"user": mechanic.user, "request": new_request},
            recipient_list=[mechanic.user.email],
        )
        send_html_email(
            subject=f"{driver.user.first_name} sent a request to {mechanic.user.first_name}",
            template_name="mails/new_user_request.html",
            context={"driver": driver.user, "mechanic":mechanic.user, "request":new_request},
            recipient_list=[settings.EMAIL_HOST_NAME],
        )
        messages.success(request, "Request sent successfully!")
        try:
            url = f"{settings.TERMII_BASE_URL}/api/sms/send"
            payload = {
                    "to": mechanic.mobile,
                    "from": "Ariscomart",
                    "sms": f"{driver.user.first_name} just sent you a new request with id: {new_request.id} Problem {new_request.problem_description}",
                    "type": "plain",
                    "channel": "generic",
                    "api_key": settings.TERMII_SMS_API,
                        "media": {
                            "url": "https://www.autoaid.com.ng/static/image/mail-logo.svg",
                            "caption": f"New Request Recieved from {driver.user.first_name}"
                        }   
                }
            headers = {
            'Content-Type': 'application/json',
            }
            response = requests.request("POST", url, headers=headers, json=payload)
            print(response.text)
        except Exception as e:
            print(f"An unknown error occured {e}")
        return redirect('driver-dashboard')  # Adjust as needed
    return render(request, 'driver-pro-request-send.html',{'mechanic':mechanic})
    
    


##################################
#             Mechanic           #
##################################

@login_required(login_url='login')
@user_passes_test(is_mechanic)
@email_verified_required
def mechanicDashboard(request):
    accountapproval = models.Mechanic.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        mechanic = models.Mechanic.objects.get(user_id=request.user.id)
        bill = models.Request.objects.filter(mechanic_id=mechanic.id).filter(Q(status="Released")).aggregate(Sum('cost'))
        work_in_progress = models.Request.objects.filter(mechanic_id=mechanic.id).filter(Q(status="Accepted") | Q(status="Done") | Q(status="Repairing")).count()
        work_completed = models.Request.objects.filter(mechanic_id=mechanic.id).filter(Q(status="Released")).count()
        new_job = models.Request.objects.filter(status='Approved').count()
        notifications = mechanic.mechnotifications.all().order_by('-timestamp')
        requests = models.Request.objects.filter(mechanic_id=mechanic.id).select_related('driver').order_by('-date')
        active_requests = models.Request.objects.filter(status='Approved').order_by('-date')
        accept_requests = models.Request.objects.filter(mechanic_id=mechanic.id).filter(status__in=['Accepted', 'Done', 'Repairing']).order_by('-date')
        print(bill)
        print(accept_requests)
        context = {
            'work_in_progress': work_in_progress,
            'work_completed': work_completed,
            'new_job': new_job,
            'notifications':notifications,
            'salary': mechanic.salary,
            'mechanic': mechanic,
            'requests': requests, 
            'bill': bill['cost__sum'] or 0,
            'active_requests': active_requests,
            'accept_requests': accept_requests,
        }
    else:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'mechanic-dashboard.html', context=context)

@login_required(login_url='login')
@user_passes_test(is_mechanic)
@email_verified_required
def mechanicHistory(request):
    accountapproval = models.Mechanic.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        mechanic = models.Mechanic.objects.get(user_id=request.user.id)
        requests = models.Request.objects.filter(mechanic_id=mechanic.id).select_related('driver').order_by('-date')
        context={
            'mechanic':mechanic,
            'requests':requests,
        }
    else:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'mechanic-job-history.html', context=context)

@login_required(login_url='login')
@user_passes_test(is_mechanic)
@email_verified_required
def mechanicMonthlyEarning(request, mechanic_id):
    try:
        mechanic = models.Mechanic.objects.get(user_id=request.user.id, id=mechanic_id)
    except models.Mechanic.DoesNotExist:
        return HttpResponseForbidden("You are not authorized to access this data.")

    # Fetch current year and mechanic's requests
    current_date = localtime(timezone.now())
    current_year = current_date.year
    requests = (
        models.Request.objects.filter(
            mechanic_id=mechanic_id,
            status__in=["Done", "Released"],
            date__year=current_year,
        )
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total_earnings=Sum('cost'))
        .order_by('month')
    )

    monthly_earnings_map = {
        entry['month'].month: entry['total_earnings'] for entry in requests
    }

    monthly_earnings = [
        {
            "month": calendar.month_name[month],
            "earnings": monthly_earnings_map.get(month, 0)
        }
        for month in range(1, 13)
    ]

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(monthly_earnings, safe=False)
    else:
        return HttpResponseBadRequest("This endpoint only supports AJAX requests.")


# def mechanicMonthlyEarning(request, mechanic_id):
#     try:
#         mechanic = models.Mechanic.objects.get(user_id=request.user.id, id=mechanic_id)
#     except models.Mechanic.DoesNotExist:
#         return HttpResponseForbidden("You are not authorized to access this data.")

#     # Fetch current year and mechanic's requests
#     current_date = timezone.now()
#     current_year = current_date.year
#     requests = models.Request.objects.filter(
#         mechanic_id=mechanic_id,
#         status__in=["Done", "Released"],
#         date__year=current_year
#     ).values('date__month').annotate(total_earnings=Sum('cost'))

#     monthly_earnings_map = {entry['date__month']: entry['total_earnings'] for entry in requests}

#     monthly_earnings = [
#         {
#             "month": calendar.month_name[month],
#             "earnings": monthly_earnings_map.get(month, 0)
#         }
#         for month in range(1, 13)
#     ]

#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         return JsonResponse(monthly_earnings, safe=False)
#     else:
#         return HttpResponseBadRequest("This endpoint only supports AJAX requests.")


# for month in range(1, 13):
#             total_earnings = models.Request.objects.filter(
#                 mechanic_id=mechanic_id,
#                 status__in=["Released"],
#                 date__year=current_year,
#                 date__month=month
#             ).aggregate(total=Sum('cost'))['total'] or 0
            
#             month_name = datetime(current_year, month, 1).strftime('%B')
#             monthly_earnings.append({"month": month_name, "earnings": total_earnings})
#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             return JsonResponse(monthly_earnings, safe=False)
# current_year = current_date.year
#         monthly_earnings = []

@login_required(login_url='login')
@user_passes_test(is_mechanic)
@email_verified_required
def mechanicEarning(request):
    accountapproval = models.Mechanic.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        current_date = timezone.now()
        mechanic = models.Mechanic.objects.get(user_id=request.user.id)
        requests = models.Request.objects.filter(mechanic_id=mechanic.id).select_related('driver').order_by('-date')
        pending_bill = models.Request.objects.filter(mechanic_id=mechanic.id).filter(Q(status="Accepted") | Q(status="Done") | Q(status="Repairing")).aggregate(Sum('cost'))
        bill = models.Request.objects.filter(mechanic_id=mechanic.id).filter(Q(status="Released")).aggregate(Sum('cost'))
        withdrawal_history = models.MechanicWithdrawalHistory.objects.filter(mechanic_id=mechanic.id).order_by('-date')
        month_bill = models.Request.objects.filter(
            mechanic_id=mechanic.id,
            status__in=["Released"],
            date__year=current_date.year,
            date__month=current_date.month
        ).aggregate(Sum('cost'))
        context = {
            'bill': bill['cost__sum'] or 0,
            'month_bill': month_bill['cost__sum'] or 0,
            'pending_bill': pending_bill['cost__sum'] or 0,
            'mechanic': mechanic,
            'salary': mechanic.salary or 0,
            'requests': requests,
            'withdrawal_history': withdrawal_history,
        }
        return render(request, 'mechanic-earning.html', context=context)
    else:
        return HttpResponseRedirect('afterlogin')


@login_required(login_url='login')
@user_passes_test(is_mechanic)
@email_verified_required
def mechanicWithdraw(request):
    account_approval = models.Mechanic.objects.filter(user_id=request.user.id, status=True).exists()
    if account_approval:
        mechanic = models.Mechanic.objects.get(user_id=request.user.id)
        if request.method == "POST":
            if mechanic.account_number and mechanic.bank_code:
                # Generate unique transaction reference
                timestamp = str(calendar.timegm(time.gmtime()))
                unique_string = f"{mechanic.id}{timestamp}"
                transaction_ref = f"TXN{mechanic.id}{hashlib.sha256(unique_string.encode()).hexdigest()[:10]}"

                # Fetch and validate withdrawal amount
                try:
                    withdrawal_amount = float(request.POST.get('amount_withdraw', 0))
                    if withdrawal_amount <= 0:
                        raise ValueError("Withdrawal amount must be greater than zero.")
                except ValueError as ve:
                    messages.warning(request, f"Invalid withdrawal amount: {ve}")
                    return HttpResponseRedirect(reverse('mechanic-profile'))

                # Apply percentage deduction
                try:
                    percentage = 1
                    final_amount = apply_percentage_discount(withdrawal_amount, percentage)
                except ValueError as e:
                    messages.warning(request, f"Invalid percentage: {e}")
                    return HttpResponseRedirect(reverse('mechanic-profile'))

                # Prepare API payload
                payload = {
                    "reference": transaction_ref,
                    "destination": {
                        "type": "bank_account",
                        "amount": int(final_amount * 100),  # Convert to kobo
                        "currency": "NGN",
                        "narration": request.POST.get('narration', "Withdrawal Payment"),
                        "bank_account": {
                            "bank": mechanic.bank_code,
                            "account": mechanic.account_number
                        },
                        "customer": {
                            "name": f"{mechanic.user.first_name} {mechanic.user.last_name}",
                            "email": mechanic.user.email
                        }
                    }
                }
                headers = {
                    "Authorization": f"Bearer {settings.KORAPAY_TEST_SECRET_KEY}",
                    "Content-Type": "application/json"
                }

                # Make API call
                try:
                    response = requests.post(
                        url="https://api.korapay.com/merchant/api/v1/transactions/disburse",
                        headers=headers,
                        data=json.dumps(payload)
                    )
                    response_data = response.json()
                    if response.status_code == 200:
                        # Deduct salary and save withdrawal history 
                        if float(mechanic.salary) >= float(withdrawal_amount):
                            mechanic.salary -= float(withdrawal_amount)
                            mechanic.save()
                            MechanicWithdrawalHistory.objects.create(
                            mechanic=mechanic,
                            account_number=mechanic.account_number,
                            bank_code=mechanic.bank_code,
                            bank_name=mechanic.bank_name,
                            account_name=mechanic.account_name,
                            transaction_reference=transaction_ref,
                            amount_withdraw=withdrawal_amount,
                            narration=request.POST.get('narration', ""),
                            amount_recieved=final_amount,
                            status="Success"
                        )
                            notify = MechanicNotification(
                                mechanic=request.user.mechanic,
                                message=f"Your withdrawal was successful with Ref ID.:{transaction_ref} to {mechanic.account_name}"
                            )
                            notify.save()
                            messages.success(request, "Withdrawal successful.")
                            return HttpResponseRedirect(reverse('mechanic-earning'))
                        else:
                            messages.warning(request, "Insufficient balance for withdrawal.")
                            return HttpResponseRedirect(reverse('mechanic-earning'))
                    else:
                        print("API Error:", response_data)
                        MechanicWithdrawalHistory.objects.create(
                            mechanic=mechanic,
                            account_number=mechanic.account_number,
                            bank_code=mechanic.bank_code,
                            bank_name=mechanic.bank_name,
                            account_name=mechanic.account_name,
                            transaction_reference=transaction_ref,
                            amount_withdraw=withdrawal_amount,
                            narration=request.POST.get('narration', ""),
                            amount_recieved=final_amount,
                            status="Failed"
                        )
                        messages.warning(request, f"Withdrawal failed: {response_data.get('message', 'Unknown error')}")
                except requests.exceptions.RequestException as api_error:
                    print(f"API Error: {api_error}")
                    messages.warning(request, "Withdrawal failed due to a connection issue.")
            else:
                messages.warning(request, "Please update your account number and bank details.")
                return HttpResponseRedirect(reverse('mechanic-profile'))

        context = {
            'mechanic': mechanic,
            'salary': mechanic.salary or 0,
        }
        return render(request, 'mechanic-withdraw.html', context)
    else:
        messages.warning(request, "You are not authorized to access this page.")
        return HttpResponseRedirect(reverse('afterlogin'))

def encryptAES256(encryptionKey, paymentData):
    try:
        iv = Random.get_random_bytes(16)
        encObj = AES.new(encryptionKey.encode("utf8"), AES.MODE_GCM, iv)
        cipherText,authTag = encObj.encrypt_and_digest(paymentData.encode("utf8"))        
        iv64 = base64.b64encode(iv).decode('ascii')
        ivToHex = hexa(iv).decode()
        cipherTextToHex = hexa(cipherText).decode()
        authTagToHex = hexa(authTag).decode()
        result = ivToHex + ":" + cipherTextToHex + ":" + authTagToHex
        return result
    except Exception as e:
        print(e)

@login_required(login_url='login')
@user_passes_test(is_mechanic)
@email_verified_required
def mechanicAccept(request, request_id):
    accountapproval = models.Mechanic.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        mechanic = models.Mechanic.objects.get(user_id=request.user.id)
        accept_detail = get_object_or_404(Request, pk=request_id)
        if request.method == 'POST':
            form = MechanicAcceptStatusForm(request.POST)
            if form.is_valid():
                try:
                    if Request.objects.filter(mechanic=request.user.mechanic, status="Accepted").exists():
                        messages.warning(request, "You have an Accepted request finish up to accept a new request")
                        return redirect('mechanic-dashboard')
                    elif Request.objects.filter(mechanic=request.user.mechanic, status="Repairing").exists():
                        messages.warning(request, "You have a request in Repairing finish up to accept a new request")
                        return redirect('mechanic-dashboard')
                    elif Request.objects.filter(mechanic=request.user.mechanic, status="Done").exists():
                        messages.warning(request, "You have an Done request, release it to accept a new request!")
                        return redirect('mechanic-dashboard')
                    elif accept_detail.status == 'Accepted':
                        messages.warning(request, "This Request is already handled by someone else, please try another request!")
                        return redirect('mechanic-dashboard')
                    else:
                        accept_detail.status = 'Accepted'
                        accept_detail.mechanic_location = request.POST.get('mechanic_location')
                        accept_detail.mechanic_mobile = request.POST.get('mechanic_mobile')
                        accept_detail.mechanic = mechanic
                        accept_detail.save()
                        notify = MechanicNotification(
                            mechanic=request.user.mechanic,
                            message=f"You just accepted a request with id: {request_id}"
                        )
                        send_html_email(
                            subject=f"Request Accepted by {accept_detail.mechanic.user.first_name}",
                            template_name="mails/request_accepted.html",
                            context={"user": accept_detail.driver.user, "request": accept_detail},
                            recipient_list=[accept_detail.driver.user.email],
                        )
                        notify.save()
                        return HttpResponseRedirect(reverse('mechanic-dashboard'))
                except Exception as e:
                    messages.warning(request, f"An error occured Details: {e}")
        else:
            form = MechanicAcceptStatusForm()
    else:
        return HttpResponseRedirect(reverse('afterlogin'))
    print(form.errors)
    return render(request, 'mechanic-request-accept.html', {'mechanic': mechanic, 'accept_detail': accept_detail, 'form': form})

@login_required(login_url='login')
@user_passes_test(is_mechanic)
@request_assigned_to_user
@email_verified_required
def mechanicRelease(request, request_id):
    accountapproval = models.Mechanic.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        mechanic = models.Mechanic.objects.get(user_id=request.user.id)
        accept_detail = get_object_or_404(Request, pk=request_id)
        if request.method == 'POST':
            accept_detail.mechanic = mechanic
            accept_detail.status = 'Released'
            accept_detail.invoice = 'Paid'
            accept_detail.method = 'Cash'
            accept_detail.save()
            notify = MechanicNotification(
                mechanic=request.user.mechanic,
                message=f"You changed a request status to {accept_detail.status} with id: {request_id}"
            )
            notify.save()

            return HttpResponseRedirect(reverse('mechanic-dashboard'))
        else:
            messages.info(request, "Make sure to confirm payment before Releasing a request!")
    else:
        return HttpResponseRedirect(reverse('afterlogin'))
    return render(request, 'mechanic-request-release.html', {'mechanic': mechanic, 'accept_detail': accept_detail})

@login_required(login_url='login')
@user_passes_test(is_mechanic)
@request_assigned_to_user
@email_verified_required
def mechanicDone(request, request_id):
    accountapproval = models.Mechanic.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        mechanic = models.Mechanic.objects.get(user_id=request.user.id)
        accept_detail = get_object_or_404(Request, pk=request_id)
        new_date = timezone.now()
        
        if request.method == 'POST':
            accept_detail.mechanic = mechanic
            accept_detail.status = 'Done'
            accept_detail.estimated_completion_date = new_date
            accept_detail.eta = request.POST.get('eta')
            accept_detail.save()
            notify = MechanicNotification(
                mechanic=request.user.mechanic,
                message=f"You changed a request status to {accept_detail.status} with id: {request_id}"
                )
            notify.save()
            return HttpResponseRedirect(reverse('mechanic-dashboard'))
        else:
            messages.info(request, "Finish up before marking a request as Done")
    else:
        return HttpResponseRedirect(reverse('afterlogin'))
    return render(request, 'mechanic-request-done.html', {'mechanic': mechanic, 'accept_detail': accept_detail})

@login_required(login_url='login')
@user_passes_test(is_mechanic)
@request_assigned_to_user
@email_verified_required
def mechanicCancel(request, request_id):
    accountapproval = models.Mechanic.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        mechanic = models.Mechanic.objects.get(user_id=request.user.id)
        accept_detail = get_object_or_404(Request, pk=request_id)
        if request.method == 'POST':
            accept_detail.status = 'Approved'
            accept_detail.save()
            notify = MechanicNotification(
                mechanic=request.user.mechanic,
                message=f"You canceled a request with id: {request_id}"
                )
            notify.save()
            return HttpResponseRedirect(reverse('mechanic-dashboard'))
        else:
            messages.info(request, "Request status still active")
    else:
        return HttpResponseRedirect(reverse('afterlogin'))
    return render(request, 'mechanic-request-cancel.html', {'mechanic': mechanic, 'accept_detail': accept_detail})

@login_required(login_url='login')
@user_passes_test(is_mechanic)
@request_assigned_to_user
@email_verified_required
def mechanicUpdate(request, request_id):
    accountapproval = models.Mechanic.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        mechanic = models.Mechanic.objects.get(user_id=request.user.id)
        accept_detail = get_object_or_404(Request, pk=request_id)
        if request.method == 'POST':
            form = MechanicUpdateStatusForm(request.POST)
            if form.is_valid():
                accept_detail.cost = form.cleaned_data['cost']
                accept_detail.status = 'Repairing'
                accept_detail.save()
                notify = MechanicNotification(
                    mechanic=request.user.mechanic,
                    message=f"You changed a request status to {accept_detail.status} with id: {request_id}"
                )
                notify.save()

                return HttpResponseRedirect(reverse('mechanic-dashboard'))
        else:
            form = MechanicUpdateStatusForm()
    else:
        return HttpResponseRedirect(reverse('afterlogin'))
    return render(request, 'mechanic-request-update.html', {'mechanic': mechanic, 'accept_detail': accept_detail, 'form': form})

@login_required(login_url='login')
@user_passes_test(is_mechanic)
@email_verified_required
def mechanicProfile(request):
    account_approval = models.Mechanic.objects.filter(user_id=request.user.id, status=True).exists()
    if account_approval:
        mechanic = models.Mechanic.objects.get(user_id=request.user.id)
        user = models.User.objects.get(id=mechanic.user_id)
        serviceForm = forms.ServiceFrom(
            initial={service: True for service in mechanic.service.split(', ')}
        )
         # Fetch bank data from API
        # banks = [
        #     {"name": "Access Bank", "code": "044"},
        #     {"name": "GTBank", "code": "058"},
        #     # Add more banks here
        # ]
        # json_file_path = os.path.join(settings.BASE_DIR, 'data', 'banks.json')
        # # Load JSON data
        # with open(json_file_path, 'r') as file:
        #     banks = json.load(file)

        banks=fetch_banks()
        
        # response = requests.get("https://example.com/banks.json")
        # banks = response.json()

        if request.method == 'POST':
            userForm = forms.MechanicUserForm(request.POST, instance=request.user)
            mechanicForm = forms.MechanicForm(request.POST, request.FILES, instance=mechanic)
            serviceForm = forms.ServiceFrom(request.POST)
            if 'mechanic_update_profile' in request.POST:
                if userForm.is_valid() and mechanicForm.is_valid():
                    try:
                        user = userForm.save()
                        user.set_password(userForm.cleaned_data['password'])
                        user.save()
                        messages.success(request, "Profile updated successfully!")
                        return redirect('mechanic-profile')
                    except Exception as e:
                        messages.warning(request, f"An error occurred! Detail: {e}")
                        return redirect('mechanic-profile')
                else:
                    messages.warning(request, "Invalid form data for profile update.")
            elif 'service_form' in request.POST:
                if serviceForm.is_valid():
                    try:
                        selected_services = [key for key, value in serviceForm.cleaned_data.items() if value]
                        mechanic.service = ', '.join(selected_services)
                        mechanic.save()
                        messages.success(request, "Services updated successfully!")
                        return redirect('mechanic-profile')
                    except Exception as e:
                        messages.warning(request, f"An error occurred! Detail: {e}")
                        return redirect('mechanic-profile')
                else:
                    messages.warning(request, "Invalid service form data.")
            elif 'mechanic_update' in request.POST:
                if mechanicForm.is_valid():
                    try:
                        user = mechanicForm.save()
                        user.save()
                        messages.success(request, "Profile Details updated successfully!")
                        return redirect('mechanic-profile')
                    except Exception as e:
                        messages.warning(request, f"An error occurred! Detail: {e}")
                        return redirect('mechanic-profile')
                else:
                    messages.warning(request, "Invalid service form data.")
            
            # If form is submitted
            elif 'account_detail' in request.POST:
                account_number = request.POST.get("account_number")
                bank_code = request.POST.get("bank_code")  # Corrected field name for bank_code
                # Validate inputs
                if not account_number or not bank_code:
                    messages.warning(request, "Please provide both account number and bank code.")
                else:
                    # Call the verification function
                    verification_result = verify_account(account_number, bank_code, "NGN")  # Assuming "NG" for Nigerian currency

                    if verification_result.get("status"):  # Safely check for the status key
                        try:
                            mechanic.account_name = verification_result["data"]["account_name"]
                            mechanic.account_number = account_number
                            mechanic.bank_code = bank_code
                            mechanic.currency = "NGN"
                            mechanic.bank_name = verification_result["data"]["bank_name"]
                            mechanic.save()
                            messages.success(request, "Account details updated successfully!")
                            return redirect('mechanic-profile')
                        except AttributeError:
                            messages.warning(request, "Unable to update account details. Please ensure you are logged in as a mechanic.")
                            return redirect('mechanic-profile')
                    else:
                        # Display the error message from the API response
                        error_message = verification_result.get("message", "Verification failed. Please try again.")
                        messages.warning(request, error_message)
                        return redirect('mechanic-profile')
        else:
            userForm = forms.MechanicUserForm(instance=request.user)
            mechanicForm = forms.MechanicForm(instance=mechanic)
        context = {
            'mechanic': mechanic,
            'userForm': userForm,
            'mechanicForm': mechanicForm,
            'serviceForm': serviceForm,
            'banks':banks,
        }
    else:
        return HttpResponseRedirect(reverse('afterlogin'))
    return render(request, 'mechanic-profile.html', context=context)

@csrf_exempt
def account_verification_view(request):
    if request.method == "POST":
        try:
            # Log the raw request body for debugging
            logger.info(f"Request body: {request.body}")
            data = json.loads(request.body)

            # Extract account number and bank code
            account_number = data.get("account_number")
            bank_code = data.get("bank_code")
            currency = data.get("currency", "NGN")  # Default currency to "NG" if not provided
            logger.info(f"Account Number: {account_number}, Bank Code: {bank_code}, Currency: {currency}")

            # Validate inputs
            if not account_number or not bank_code or not currency:
                return JsonResponse(
                    {"status": False, "message": "Account number, bank code, and currency are required"},
                    status=400,
                )

            # Call the verification function
            verification_result = verify_account(account_number, bank_code, currency)

            if verification_result["status"]:
                return JsonResponse(
                    {"status": True, "message": "Account verified", "data": verification_result["data"]},
                    status=200,
                )
            else:
                return JsonResponse(
                    {"status": False, "message": verification_result["message"]},
                    status=400,
                )
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return JsonResponse({"status": False, "message": str(e)}, status=500)
    else:
        return JsonResponse({"status": False, "message": "Invalid request method"}, status=405)

def verify_account(account_number, bank_code, currency):
    """
    Function to verify a customer's account number and bank code using Korapay's API.
    """
    url = f"{settings.KORAPAY_BASE_URL}/merchant/api/v1/misc/banks/resolve"
    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "bank": bank_code,
        "account": account_number,
        "currency": currency,  # Add currency to payload
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        logger.info(f"Korapay API Response: {response.status_code}, Body: {response.text}")
        response_data = response.json()

        if response.status_code == 200 and response_data.get("status"):
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
        logger.error(f"Error communicating with Korapay: {e}")
        return {"status": False, "message": str(e)}

def fetch_banks():
    url = "https://api.korapay.com/merchant/api/v1/misc/banks?countryCode=NG"
    headers = {
        "Authorization": "Bearer pk_live_hhE5aFcwbFivmzBFAEHPktwYZahUQCx6z7CFVijJ",  # Replace with your actual public key
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("status"):
                return data["data"]  # List of banks
            else:
                return []
        else:
            print(f"Failed to fetch banks: {response.status_code} - {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while fetching banks: {e}")
        return []
    


#                 notix = Notix(settings.NOTIX_APP_ID, settings.NOTIX_AUTH_TOKEN)
#                 message = {
#                     "message": {
#                         "title": "Request Created",
#                         "text": f"Request for {new_request.category} at {new_request.location} have been created and awaiting admin approval."
#                     }
#                 }
#                 try:
#                     response = notix.send_notification(message)
#                     if response.get('status_code') != 200:
#                         print(f"Push Notification Error: {response}")
#                     else:
#                         print("Push Notification Sent:", response)
#                 except Exception as e:
#                     print(f"Failed to send push notification: {e}")



##################################
#             Manager           #
##################################


def managerRegister(request):
    if request.method == 'POST':
        user_form = ManagerUserForm(request.POST)
        manager_form = ManagerForm(request.POST, request.FILES)

        if user_form.is_valid() and manager_form.is_valid():
            try:
                # Create the User instance
                user = user_form.save(commit=False)
                user.set_password(user_form.cleaned_data['password']) 
                user.save()

                manager = manager_form.save(commit=False)
                manager.user = user
                manager.save()

                manager_group, created = Group.objects.get_or_create(name='MANAGER')
                manager_group.user_set.add(user)

                msg1 = "Verify Your Email"
                msg2 = "Click the link below to verify your email:"
                token = generate_token(user.email)
                verification_link = f"{settings.SITE_URL}/verify-email/{token}"
                send_html_email(
                    subject="Welcome to Auto Aid",
                    template_name="mails/verify.html",
                    context={"user": user, "message1":msg1, "message2":msg2, "link":verification_link},
                    recipient_list=[user.email],
                )
                messages.success(request, 'Registration successful.')
                return render(request, 'registration_pending.html', {'current_year': datetime.now().year})
            except Exception as e:
                messages.warning(request, f"An Error occurred: {e}")
                print(f"An Error occurred: {e}")
        else:
            messages.warning(request, 'Please correct the errors below.')

    else:
        user_form = ManagerUserForm()
        manager_form = ManagerForm()

    return render(request, 'manager-register.html', {
        'user_form': user_form,
        'manager_form': manager_form,
    })


@login_required(login_url='login')
@user_passes_test(is_manager)
@email_verified_required
def managerDashboard(request):
    accountapproval = models.Manager.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        manager = models.Manager.objects.get(user_id=request.user.id)
        bill = models.Request.objects.filter(manager_id=manager.id).filter(Q(status="Released")).aggregate(Sum('cost'))
        work_in_progress = models.Request.objects.filter(manager_id=manager.id).filter(Q(status="Accepted") | Q(status="Done") | Q(status="Repairing")).count()
        work_completed = models.Request.objects.filter(manager_id=manager.id).filter(Q(status="Released")).count()
        new_job = models.Request.objects.filter(status='Approved').count()
        notifications = manager.mannotifications.all().order_by('-timestamp')
        requests = models.Request.objects.filter(manager_id=manager.id).select_related('driver').order_by('-date')
        active_requests = models.Request.objects.filter(status='Pending').order_by('-date')
        accept_requests = models.Request.objects.filter(manager_id=manager.id).filter(status__in=['Accepted', 'Done', 'Repairing']).order_by('-date')
        print(bill)
        print(accept_requests)
        context = {
            'work_in_progress': work_in_progress,
            'work_completed': work_completed,
            'new_job': new_job,
            'notifications':notifications,
            'salary': manager.salary,
            'manager': manager,
            'requests': requests, 
            'bill': bill['cost__sum'] or 0,
            'active_requests': active_requests,
            'accept_requests': accept_requests,
        }
    else:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'manager-dashboard.html', context=context)

@login_required(login_url='login')
@user_passes_test(is_manager)
@email_verified_required
def managerMechanic(request):
    accountapproval = models.Manager.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        manager = models.Manager.objects.get(user_id=request.user.id)
        mechanics = models.Mechanic.objects.filter(my_manager=manager)
        state = request.GET.get('state')
        local_government = request.GET.get('local_government')
        if state:
            mechanics = mechanics.filter(state=state)
        if local_government:
            mechanics = mechanics.filter(local_government=local_government)
        work_completed = {}
        for mechanic in mechanics:
            count = models.Request.objects.filter(
                mechanic_id=mechanic.id, status__iexact="Released"
            ).count()
            work_completed[mechanic.id] = count
            print(f"Mechanic ID: {mechanic.id}, Completed Jobs: {count}")  # Debugging

        work_in_progress = {}
        for mechanic in mechanics:
            count = models.Request.objects.filter(
                mechanic_id=mechanic.id,
            ).filter(Q(status="Accepted") | Q(status="Done") | Q(status="Repairing")).count()
            work_in_progress[mechanic.id] = count  # Fix here
            print(f"Mechanic ID: {mechanic.id}, In-progress Jobs: {count}")  # Debugging

        return render(request, 'manager-mechanic.html', {
            'mechanics': mechanics,
            'manager': manager,
            'work_completed': work_completed,
            'work_in_progress':work_in_progress
        })
    else:
        return HttpResponseRedirect('afterlogin')

@login_required(login_url='login')
@user_passes_test(is_manager)
@email_verified_required
def managerOnboard(request):
    accountapproval = models.Manager.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        manager = models.Manager.objects.get(user_id=request.user.id)
        mechanics = models.Mechanic.objects.filter(my_manager=None)
        state = request.GET.get('state')
        local_government = request.GET.get('local_government')
        if state:
            mechanics = mechanics.filter(state=state)
        if local_government:
            mechanics = mechanics.filter(local_government=local_government)
        work_completed = {}
        for mechanic in mechanics:
            count = models.Request.objects.filter(
                mechanic_id=mechanic.id, status__iexact="Released"
            ).count()
            work_completed[mechanic.id] = count
            print(f"Mechanic ID: {mechanic.id}, Completed Jobs: {count}")  # Debugging

        work_in_progress = {}
        for mechanic in mechanics:
            count = models.Request.objects.filter(
                mechanic_id=mechanic.id,
            ).filter(Q(status="Accepted") | Q(status="Done") | Q(status="Repairing")).count()
            work_in_progress[mechanic.id] = count  # Fix here
            print(f"Mechanic ID: {mechanic.id}, In-progress Jobs: {count}")  # Debugging

        return render(request, 'manager-onboard.html', {
            'mechanics': mechanics,
            'manager': manager,
            'work_completed': work_completed,
            'work_in_progress':work_in_progress
        })
    else:
        return HttpResponseRedirect('afterlogin')

@login_required(login_url='login')
@user_passes_test(is_manager)
@email_verified_required
def managerApprove(request, mechanic_id):
    # Check if manager account is approved
    accountapproval = models.Manager.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        mechanic = get_object_or_404(models.Mechanic, id=mechanic_id)
        manager = get_object_or_404(models.Manager, user_id=request.user.id)

        if request.method == "POST":
            if 'approve' in request.POST:
                try:
                    # Approve mechanic
                    mechanic.status = True
                    mechanic.save()

                    # Notify manager
                    ManagerNotification.objects.create(
                        manager=request.user.manager,
                        message="You just approved a mechanic."
                    )

                    # Notify mechanic
                    MechanicNotification.objects.create(
                        mechanic=mechanic,
                        message=f"{manager.user.first_name} just approved you."
                    )

                    # Send approval emails
                    send_html_email(
                        subject=f"{manager.user.first_name} just approved you",
                        template_name="mails/manager_approve.html",
                        context={"user": mechanic.user},
                        recipient_list=[mechanic.user.email],
                    )
                    send_html_email(
                        subject=f"{manager.user.first_name} approved {mechanic.user.first_name}",
                        template_name="mails/admin_manager_approve.html",
                        context={"user": mechanic.user, "manager": manager.user},
                        recipient_list=[settings.EMAIL_HOST_NAME],
                    )

                    # Send SMS notification
                    try:
                        url = f"{settings.TERMII_BASE_URL}/api/sms/send"
                        payload = {
                            "to": mechanic.mobile,
                            "from": "Auto Aid",
                            "sms": "You have been approved to join Auto Aid. Welcome aboard!",
                            "type": "plain",
                            "channel": "generic",
                            "api_key": settings.TERMII_SMS_API,
                            "media": {
                                "url": "https://www.autoaid.com.ng/static/image/mail-logo.svg",
                                "caption": "Welcome to Auto Aid"
                            }
                        }
                        headers = {'Content-Type': 'application/json'}
                        response = requests.post(url, headers=headers, json=payload)
                        print(f"SMS Response: {response.text}")
                    except Exception as e:
                        print(f"Error sending SMS: {e}")
                    messages.success(request, "Mechanic approved successfully.")
                except Exception as e:
                    messages.warning(request, f"An error occurred: {e}")

            elif 'manage' in request.POST:
                try:
                    # Assign manager to mechanic
                    mechanic.my_manager = manager
                    mechanic.save()

                    # Notify manager
                    ManagerNotification.objects.create(
                        manager=request.user.manager,
                        message=f"You are now managing {mechanic.user.first_name}."
                    )

                    # Notify mechanic
                    MechanicNotification.objects.create(
                        mechanic=mechanic,
                        message=f"{manager.user.first_name} is now your manager."
                    )

                    # Send management emails
                    send_html_email(
                        subject=f"{manager.user.first_name} is now managing you",
                        template_name="mails/manager_manage.html",
                        context={"user": mechanic.user, "manager": manager.user},
                        recipient_list=[mechanic.user.email],
                    )
                    send_html_email(
                        subject=f"{manager.user.first_name} started managing {mechanic.user.first_name}",
                        template_name="mails/admin_manager_manage.html",
                        context={"user": mechanic.user, "manager": manager.user},
                        recipient_list=[settings.EMAIL_HOST_NAME],
                    )

                    messages.success(request, f"You are now managing {mechanic.user.first_name} {mechanic.user.last_name}.")
                except Exception as e:
                    messages.warning(request, f"An error occurred: {e}")

            return redirect('manager-mechanic')  # Adjust this redirect if needed

        return render(request, 'manager-approve.html', {'mechanic': mechanic, "manager":manager})
    else:
        return HttpResponseRedirect('afterlogin')

@login_required(login_url='login')
@user_passes_test(is_manager)
@email_verified_required
def managerHistory(request):
    accountapproval = models.Manager.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        manager = models.Manager.objects.get(user_id=request.user.id)
        requests = models.Request.objects.filter(manager_id=manager.id).select_related('driver').order_by('-date')
        context={
            'manager':manager,
            'requests':requests,
        }
    else:
        return HttpResponseRedirect('afterlogin')
    return render(request, 'manager-job-history.html', context=context)

@login_required(login_url='login')
@user_passes_test(is_manager)
@email_verified_required
def managerMonthlyEarning(request, manager_id):
    try:
        manager = models.Manager.objects.get(user_id=request.user.id, id=manager_id)
    except models.Manager.DoesNotExist:
        return HttpResponseForbidden("You are not authorized to access this data.")

    # Fetch current year and manager's requests
    current_date = timezone.now()
    current_year = current_date.year
    requests = models.Request.objects.filter(
        manager_id=manager_id,
        status__in=["Done", "Released"],
        date__year=current_year
    ).values('date__month').annotate(total_earnings=Sum('cost'))

    monthly_earnings_map = {entry['date__month']: entry['total_earnings'] for entry in requests}

    monthly_earnings = [
        {
            "month": calendar.month_name[month],
            "earnings": monthly_earnings_map.get(month, 0)
        }
        for month in range(1, 13)
    ]

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(monthly_earnings, safe=False)
    else:
        return HttpResponseBadRequest("This endpoint only supports AJAX requests.")


# for month in range(1, 13):
#             total_earnings = models.Request.objects.filter(
#                 manager_id=manager_id,
#                 status__in=["Released"],
#                 date__year=current_year,
#                 date__month=month
#             ).aggregate(total=Sum('cost'))['total'] or 0
            
#             month_name = datetime(current_year, month, 1).strftime('%B')
#             monthly_earnings.append({"month": month_name, "earnings": total_earnings})
#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             return JsonResponse(monthly_earnings, safe=False)
# current_year = current_date.year
#         monthly_earnings = []

@login_required(login_url='login')
@user_passes_test(is_manager)
@email_verified_required
def managerEarning(request):
    accountapproval = models.Manager.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        current_date = timezone.now()
        manager = models.Manager.objects.get(user_id=request.user.id)
        requests = models.Request.objects.filter(manager_id=manager.id).select_related('driver').order_by('-date')
        pending_bill = models.Request.objects.filter(manager_id=manager.id).filter(Q(status="Accepted") | Q(status="Done") | Q(status="Repairing")).aggregate(Sum('cost'))
        bill = models.Request.objects.filter(manager_id=manager.id).filter(Q(status="Released")).aggregate(Sum('cost'))
        withdrawal_history = models.ManagerWithdrawalHistory.objects.filter(manager_id=manager.id).order_by('-date')
        month_bill = models.Request.objects.filter(
            manager_id=manager.id,
            status__in=["Released"],
            date__year=current_date.year,
            date__month=current_date.month
        ).aggregate(Sum('cost'))
        context = {
            'bill': bill['cost__sum'] or 0,
            'month_bill': month_bill['cost__sum'] or 0,
            'pending_bill': pending_bill['cost__sum'] or 0,
            'manager': manager,
            'salary': manager.salary or 0,
            'requests': requests,
            'withdrawal_history': withdrawal_history,
        }
        return render(request, 'manager-earning.html', context=context)
    else:
        return HttpResponseRedirect('afterlogin')


@login_required(login_url='login')
@user_passes_test(is_manager)
@email_verified_required
def managerWithdraw(request):
    account_approval = models.Manager.objects.filter(user_id=request.user.id, status=True).exists()
    if account_approval:
        manager = models.Manager.objects.get(user_id=request.user.id)
        if request.method == "POST":
            if manager.account_number and manager.bank_code:
                # Generate unique transaction reference
                timestamp = str(calendar.timegm(time.gmtime()))
                unique_string = f"{manager.id}{timestamp}"
                transaction_ref = f"TXN{manager.id}{hashlib.sha256(unique_string.encode()).hexdigest()[:10]}"

                # Fetch and validate withdrawal amount
                try:
                    withdrawal_amount = float(request.POST.get('amount_withdraw', 0))
                    if withdrawal_amount <= 0:
                        raise ValueError("Withdrawal amount must be greater than zero.")
                except ValueError as ve:
                    messages.warning(request, f"Invalid withdrawal amount: {ve}")
                    return HttpResponseRedirect(reverse('manager-profile'))

                # Apply percentage deduction
                try:
                    percentage = 1
                    final_amount = apply_percentage_discount(withdrawal_amount, percentage)
                except ValueError as e:
                    messages.warning(request, f"Invalid percentage: {e}")
                    return HttpResponseRedirect(reverse('manager-profile'))

                # Prepare API payload
                payload = {
                    "reference": transaction_ref,
                    "destination": {
                        "type": "bank_account",
                        "amount": int(final_amount * 100),  # Convert to kobo
                        "currency": "NGN",
                        "narration": request.POST.get('narration', "Withdrawal Payment"),
                        "bank_account": {
                            "bank": manager.bank_code,
                            "account": manager.account_number
                        },
                        "customer": {
                            "name": f"{manager.user.first_name} {manager.user.last_name}",
                            "email": manager.user.email
                        }
                    }
                }
                headers = {
                    "Authorization": f"Bearer {settings.KORAPAY_TEST_SECRET_KEY}",
                    "Content-Type": "application/json"
                }

                # Make API call
                try:
                    response = requests.post(
                        url="https://api.korapay.com/merchant/api/v1/transactions/disburse",
                        headers=headers,
                        data=json.dumps(payload)
                    )
                    response_data = response.json()
                    if response.status_code == 200:
                        # Deduct salary and save withdrawal history 
                        if float(manager.salary) >= float(withdrawal_amount):
                            manager.salary -= float(withdrawal_amount)
                            manager.save()
                            ManagerWithdrawalHistory.objects.create(
                            manager=manager,
                            account_number=manager.account_number,
                            bank_code=manager.bank_code,
                            bank_name=manager.bank_name,
                            account_name=manager.account_name,
                            transaction_reference=transaction_ref,
                            amount_withdraw=withdrawal_amount,
                            narration=request.POST.get('narration', ""),
                            amount_recieved=final_amount,
                            status="Success"
                        )
                            notify = ManagerNotification(
                                manager=request.user.manager,
                                message=f"Your withdrawal was successful with Ref ID.:{transaction_ref} to {manager.account_name}"
                            )
                            notify.save()
                            messages.success(request, "Withdrawal successful.")
                            return HttpResponseRedirect(reverse('manager-earning'))
                        else:
                            messages.warning(request, "Insufficient balance for withdrawal.")
                            return HttpResponseRedirect(reverse('manager-earning'))
                    else:
                        print("API Error:", response_data)
                        ManagerWithdrawalHistory.objects.create(
                            manager=manager,
                            account_number=manager.account_number,
                            bank_code=manager.bank_code,
                            bank_name=manager.bank_name,
                            account_name=manager.account_name,
                            transaction_reference=transaction_ref,
                            amount_withdraw=withdrawal_amount,
                            narration=request.POST.get('narration', ""),
                            amount_recieved=final_amount,
                            status="Failed"
                        )
                        messages.warning(request, f"Withdrawal failed: {response_data.get('message', 'Unknown error')}")
                except requests.exceptions.RequestException as api_error:
                    print(f"API Error: {api_error}")
                    messages.warning(request, "Withdrawal failed due to a connection issue.")
            else:
                messages.warning(request, "Please update your account number and bank details.")
                return HttpResponseRedirect(reverse('manager-profile'))

        context = {
            'manager': manager,
            'salary': manager.salary or 0,
        }
        return render(request, 'manager-withdraw.html', context)
    else:
        messages.warning(request, "You are not authorized to access this page.")
        return HttpResponseRedirect(reverse('afterlogin'))

def encryptAES256(encryptionKey, paymentData):
    try:
        iv = Random.get_random_bytes(16)
        encObj = AES.new(encryptionKey.encode("utf8"), AES.MODE_GCM, iv)
        cipherText,authTag = encObj.encrypt_and_digest(paymentData.encode("utf8"))        
        iv64 = base64.b64encode(iv).decode('ascii')
        ivToHex = hexa(iv).decode()
        cipherTextToHex = hexa(cipherText).decode()
        authTagToHex = hexa(authTag).decode()
        result = ivToHex + ":" + cipherTextToHex + ":" + authTagToHex
        return result
    except Exception as e:
        print(e)

@login_required(login_url='login')
@user_passes_test(is_manager)
@email_verified_required
def managerAccept(request, request_id):
    accountapproval = models.Manager.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        manager = models.Manager.objects.get(user_id=request.user.id)
        mechanics = models.Mechanic.objects.filter(my_manager=manager)
        accept_detail = get_object_or_404(Request, pk=request_id)
        if request.method == 'POST':
            try:
                if Request.objects.filter(manager=request.user.manager, status="Accepted").exists():
                    messages.warning(request, "You have an Accepted request finish up to accept a new request")
                    return redirect('manager-dashboard')
                elif Request.objects.filter(manager=request.user.manager, status="Repairing").exists():
                    messages.warning(request, "You have a request in Repairing finish up to accept a new request")
                    return redirect('manager-dashboard')
                elif Request.objects.filter(manager=request.user.manager, status="Done").exists():
                    messages.warning(request, "You have an Done request, release it to accept a new request!")
                    return redirect('manager-dashboard')
                elif accept_detail.status == 'Accepted':
                    messages.warning(request, "This Request is already handled by someone else, please try another request!")
                    return redirect('manager-dashboard')
                else:
                    mechanic_id = request.POST.get('mechanic')
                    if not mechanic_id:
                        messages.warning(request, "Please select a mechanic.")
                        return redirect('manager-dashboard')
                    accept_detail.status = 'Accepted'
                    accept_detail.mechanic_location = request.POST.get('mechanic_location')
                    accept_detail.mechanic_mobile = request.POST.get('mechanic_mobile')
                    accept_detail.mechanic = get_object_or_404(models.Mechanic, id=mechanic_id)
                    accept_detail.manager = manager
                    accept_detail.save()
                    notify = ManagerNotification(
                        manager=request.user.manager,
                        message=f"You assigned a request with id: {request_id} to {accept_detail.mechanic.user.first_name}"
                    )
                    notify.save()
                    notify = ManagerNotification(
                        manager=request.user.manager,
                        message=f"Your manager {accept_detail.manager.user.first_name} assigned a request to you!"
                    )
                    notify.save()
                    send_html_email(
                        subject=f"Request Accepted by {accept_detail.manager.user.first_name}",
                        template_name="mails/request_accepted.html",
                        context={"user": accept_detail.driver.user, "request": accept_detail},
                        recipient_list=[accept_detail.driver.user.email],
                    )
                    messages.success(request, "Request accepted and assigned to a mechanic")
                    return HttpResponseRedirect(reverse('manager-dashboard'))
            except Exception as e:
                messages.warning(request, f"An error occured Details: {e}")
    else:
        return HttpResponseRedirect(reverse('afterlogin'))
    return render(request, 'manager-request-accept.html', {'manager': manager, 'accept_detail': accept_detail, 'mechanics': mechanics})

@login_required(login_url='login')
@user_passes_test(is_manager)
@request_assigned_to_user
@email_verified_required
def managerRelease(request, request_id):
    accountapproval = models.Manager.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        manager = models.Manager.objects.get(user_id=request.user.id)
        accept_detail = get_object_or_404(Request, pk=request_id)
        if request.method == 'POST':
            accept_detail.manager = manager
            accept_detail.status = 'Released'
            accept_detail.invoice = 'Paid'
            accept_detail.method = 'Cash'
            accept_detail.save()
            notify = ManagerNotification(
                manager=request.user.manager,
                message=f"You changed a request status to {accept_detail.status} with id: {request_id}"
            )
            notify.save()

            return HttpResponseRedirect(reverse('manager-dashboard'))
        else:
            messages.info(request, "Make sure to confirm payment before Releasing a request!")
    else:
        return HttpResponseRedirect(reverse('afterlogin'))
    return render(request, 'manager-request-release.html', {'manager': manager, 'accept_detail': accept_detail})

@login_required(login_url='login')
@user_passes_test(is_manager)
@request_assigned_to_user
@email_verified_required
def managerDone(request, request_id):
    accountapproval = models.Manager.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        manager = models.Manager.objects.get(user_id=request.user.id)
        accept_detail = get_object_or_404(Request, pk=request_id)
        new_date = timezone.now()
        
        if request.method == 'POST':
            accept_detail.manager = manager
            accept_detail.status = 'Done'
            accept_detail.estimated_completion_date = new_date
            accept_detail.eta = request.POST.get('eta')
            accept_detail.save()
            notify = ManagerNotification(
                manager=request.user.manager,
                message=f"You changed a request status to {accept_detail.status} with id: {request_id}"
                )
            notify.save()
            return HttpResponseRedirect(reverse('manager-dashboard'))
        else:
            messages.info(request, "Finish up before marking a request as Done")
    else:
        return HttpResponseRedirect(reverse('afterlogin'))
    return render(request, 'manager-request-done.html', {'manager': manager, 'accept_detail': accept_detail})

@login_required(login_url='login')
@user_passes_test(is_manager)
@request_assigned_to_user
@email_verified_required
def managerCancel(request, request_id):
    accountapproval = models.Manager.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        manager = models.Manager.objects.get(user_id=request.user.id)
        accept_detail = get_object_or_404(Request, pk=request_id)
        if request.method == 'POST':
            accept_detail.status = 'Approved'
            accept_detail.save()
            notify = ManagerNotification(
                manager=request.user.manager,
                message=f"You canceled a request with id: {request_id}"
                )
            notify.save()
            return HttpResponseRedirect(reverse('manager-dashboard'))
        else:
            messages.info(request, "Request status still active")
    else:
        return HttpResponseRedirect(reverse('afterlogin'))
    return render(request, 'manager-request-cancel.html', {'manager': manager, 'accept_detail': accept_detail})

@login_required(login_url='login')
@user_passes_test(is_manager)
@request_assigned_to_user
@email_verified_required
def managerUpdate(request, request_id):
    accountapproval = models.Manager.objects.filter(user_id=request.user.id, status=True).exists()
    if accountapproval:
        manager = models.Manager.objects.get(user_id=request.user.id)
        accept_detail = get_object_or_404(Request, pk=request_id)
        if request.method == 'POST':
            accept_detail.cost = request.POST.get('cost')
            accept_detail.status = 'Repairing'
            accept_detail.save()
            notify = ManagerNotification(
                manager=request.user.manager,
                message=f"You changed a request status to {accept_detail.status} with id: {request_id}"
            )
            notify.save()

            return HttpResponseRedirect(reverse('manager-dashboard'))
    else:
        return HttpResponseRedirect(reverse('afterlogin'))
    return render(request, 'manager-request-update.html', {'manager': manager, 'accept_detail': accept_detail,})

@login_required(login_url='login')
@user_passes_test(is_manager)
def managerProfile(request):
    account_approval = models.Manager.objects.filter(user_id=request.user.id, status=True).exists()
    if account_approval:
        manager = models.Manager.objects.get(user_id=request.user.id)
        user = models.User.objects.get(id=manager.user_id)
        
         # Fetch bank data from API
        # banks = [
        #     {"name": "Access Bank", "code": "044"},
        #     {"name": "GTBank", "code": "058"},
        #     # Add more banks here
        # ]
        # json_file_path = os.path.join(settings.BASE_DIR, 'data', 'banks.json')
        # # Load JSON data
        # with open(json_file_path, 'r') as file:
        #     banks = json.load(file)

        banks=fetch_banks()
        
        # response = requests.get("https://example.com/banks.json")
        # banks = response.json()

        if request.method == 'POST':
            userForm = forms.ManagerUserForm(request.POST, instance=request.user)
            managerForm = forms.ManagerForm(request.POST, request.FILES, instance=manager)
            if 'manager_update_profile' in request.POST:
                if userForm.is_valid():
                    try:
                        user = userForm.save()
                        user.set_password(userForm.cleaned_data['password'])
                        user.save()
                        messages.success(request, "Profile updated successfully!")
                        return redirect('manager-profile')
                    except Exception as e:
                        messages.warning(request, f"An error occurred! Detail: {e}")
                        return redirect('manager-profile')
                else:
                    messages.warning(request, "Invalid form data for profile update.")
            elif 'manager_update' in request.POST:
                if managerForm.is_valid():
                    try:
                        user = managerForm.save()
                        user.save()
                        messages.success(request, "Profile Details updated successfully!")
                        return redirect('manager-profile')
                    except Exception as e:
                        messages.warning(request, f"An error occurred! Detail: {e}")
                        return redirect('manager-profile')
                else:
                    logger.info(f"Mechanic before update: {managerForm}")
                    messages.warning(request, "Invalid service form data.")
            
            # If form is submitted
            elif 'account_detail' in request.POST:
                account_number = request.POST.get("account_number")
                bank_code = request.POST.get("bank_code")  # Corrected field name for bank_code
                # Validate inputs
                if not account_number or not bank_code:
                    messages.warning(request, "Please provide both account number and bank code.")
                else:
                    # Call the verification function
                    verification_result = verify_account(account_number, bank_code, "NGN")  # Assuming "NG" for Nigerian currency

                    if verification_result.get("status"):  # Safely check for the status key
                        try:
                            manager.account_name = verification_result["data"]["account_name"]
                            manager.account_number = account_number
                            manager.bank_code = bank_code
                            manager.currency = "NGN"
                            manager.bank_name = verification_result["data"]["bank_name"]
                            manager.save()
                            messages.success(request, "Account details updated successfully!")
                            return redirect('manager-profile')
                        except AttributeError:
                            messages.warning(request, "Unable to update account details. Please ensure you are logged in as a manager.")
                            return redirect('manager-profile')
                    else:
                        # Display the error message from the API response
                        error_message = verification_result.get("message", "Verification failed. Please try again.")
                        messages.warning(request, error_message)
                        return redirect('manager-profile')
        else:
            userForm = forms.ManagerUserForm(instance=request.user)
            managerForm = forms.ManagerForm(instance=manager)
        context = {
            'manager': manager,
            'userForm': userForm,
            'managerForm': managerForm,
            'banks':banks,
        }
    else:
        return HttpResponseRedirect(reverse('afterlogin'))
    return render(request, 'manager-profile.html', context=context)

@csrf_exempt
def account_verification_view(request):
    if request.method == "POST":
        try:
            # Log the raw request body for debugging
            logger.info(f"Request body: {request.body}")
            data = json.loads(request.body)

            # Extract account number and bank code
            account_number = data.get("account_number")
            bank_code = data.get("bank_code")
            currency = data.get("currency", "NGN")  # Default currency to "NG" if not provided
            logger.info(f"Account Number: {account_number}, Bank Code: {bank_code}, Currency: {currency}")

            # Validate inputs
            if not account_number or not bank_code or not currency:
                return JsonResponse(
                    {"status": False, "message": "Account number, bank code, and currency are required"},
                    status=400,
                )

            # Call the verification function
            verification_result = verify_account(account_number, bank_code, currency)

            if verification_result["status"]:
                return JsonResponse(
                    {"status": True, "message": "Account verified", "data": verification_result["data"]},
                    status=200,
                )
            else:
                return JsonResponse(
                    {"status": False, "message": verification_result["message"]},
                    status=400,
                )
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return JsonResponse({"status": False, "message": str(e)}, status=500)
    else:
        return JsonResponse({"status": False, "message": "Invalid request method"}, status=405)

def verify_account(account_number, bank_code, currency):
    """
    Function to verify a customer's account number and bank code using Korapay's API.
    """
    url = f"{settings.KORAPAY_BASE_URL}/merchant/api/v1/misc/banks/resolve"
    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "bank": bank_code,
        "account": account_number,
        "currency": currency,  # Add currency to payload
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        logger.info(f"Korapay API Response: {response.status_code}, Body: {response.text}")
        response_data = response.json()

        if response.status_code == 200 and response_data.get("status"):
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
        logger.error(f"Error communicating with Korapay: {e}")
        return {"status": False, "message": str(e)}

def fetch_banks():
    url = "https://api.korapay.com/merchant/api/v1/misc/banks?countryCode=NG"
    headers = {
        "Authorization": "Bearer pk_live_hhE5aFcwbFivmzBFAEHPktwYZahUQCx6z7CFVijJ",  # Replace with your actual public key
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("status"):
                return data["data"]  # List of banks
            else:
                return []
        else:
            print(f"Failed to fetch banks: {response.status_code} - {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while fetching banks: {e}")
        return []
    


#                 notix = Notix(settings.NOTIX_APP_ID, settings.NOTIX_AUTH_TOKEN)
#                 message = {
#                     "message": {
#                         "title": "Request Created",
#                         "text": f"Request for {new_request.category} at {new_request.location} have been created and awaiting admin approval."
#                     }
#                 }
#                 try:
#                     response = notix.send_notification(message)
#                     if response.get('status_code') != 200:
#                         print(f"Push Notification Error: {response}")
#                     else:
#                         print("Push Notification Sent:", response)
#                 except Exception as e:
#                     print(f"Failed to send push notification: {e}")
