from django.http import HttpResponseForbidden
from functools import wraps
from .models import Driver, Manager, Mechanic, Request
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from datetime import datetime


def email_verified_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if the user is authenticated
        if request.user.is_authenticated:
            # Check roles and email verification
            driver = Driver.objects.filter(user=request.user, is_email_verified=True).exists()
            manager = Manager.objects.filter(user=request.user, is_email_verified=True).exists()
            mechanic = Mechanic.objects.filter(user=request.user, is_email_verified=True).exists()

            if driver or manager or mechanic:
                # Allow access if email is verified
                return view_func(request, *args, **kwargs)
        
        # Redirect to a verification page if email is not verified
            return render(request, "registration_pending.html", {'current_year': datetime.now().year})

    return _wrapped_view




def request_assigned_to_user(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        request_id = kwargs.get('request_id')  # Extract request_id from URL
        try:
            request_obj = Request.objects.get(pk=request_id)
        except Request.DoesNotExist:
            return render(request, '404.html', status=404)
            # return HttpResponseForbidden("Request not found or invalid.")
        # Check if the logged-in user is the driver or mechanic associated with the request
        if request.user.is_authenticated and (
            (request_obj.driver and request_obj.driver.user == request.user) or
            (request_obj.mechanic and request_obj.mechanic.user == request.user) or
            (request_obj.manager and request_obj.manager.user == request.user)

        ):
            return view_func(request, *args, **kwargs)
        return render(request, '403.html', status=403)
        
        # return HttpResponseForbidden("You are not authorized to access this request.")
    return _wrapped_view