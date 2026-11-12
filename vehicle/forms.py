from django import forms
from django.contrib.auth.models import User
from . import models
from .models import Request

class MechanicUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']

class MechanicForm(forms.ModelForm):
    class Meta:
        model = models.Mechanic
        fields = ['profile_pic', 'business_license', 'my_manager', 'union_name', 'union_location', 'mobile', 'address', 'state', 'local_government']

class ManagerUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput(attrs={'placeholder': 'Enter your password'}),
        }

class ManagerForm(forms.ModelForm):
    class Meta:
        model = models.Manager
        fields = [
            'state', 'local_government', 'address', 'profile_pic', 'business', 'gender', 'mobile', 'guarantor_name', 'guarantor_mobile', 
            'guarantor_email', 'guarantor_pic', 'guarantor2_name', 
            'guarantor2_mobile', 'guarantor2_email', 'guarantor2_pic'
        ]


class DriverUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']

class DriverForm(forms.ModelForm):
    class Meta:
        model = models.Driver
        fields = ['address', 'mobile', 'profile_pic', 'license_no', 'vehicle_model']

class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ['vehicle_no', 'vehicle_name', 'problem_description', 'cost', 'category', 'location', 'state', 'mobile',]  # Include necessary fields

class ServiceFrom(forms.Form):
    tire_repair = forms.BooleanField(required=False, label="Tire Repair")
    towing_service = forms.BooleanField(required=False, label="Towing Service")
    battery_jumpstart = forms.BooleanField(required=False, label="Battery Jumpstart")
    eletrical_issue = forms.BooleanField(required=False, label="Electrical Issues")
    engine_repair = forms.BooleanField(required=False, label="Engine Repair")
    body_work = forms.BooleanField(required=False, label="Bodywork/Collision Repair")
    others = forms.BooleanField(required=False, label="Other Repair Service")
    general = forms.BooleanField(required=False, label="General Mechanics/All Services")

class AdminRequestForm(forms.Form):
    #to_field_name value will be stored when form is submitted.....__str__ method of customer model will be shown there in html
    driver=forms.ModelChoiceField(queryset=models.Driver.objects.all(),empty_label="Driver Name",to_field_name='id')
    mechanic=forms.ModelChoiceField(queryset=models.Mechanic.objects.all(),empty_label="Mechanic Name",to_field_name='id')
    cost=forms.IntegerField()

class AdminApproveRequestForm(forms.Form):
    mechanic=forms.ModelChoiceField(queryset=models.Mechanic.objects.all(),empty_label="Mechanic Name",to_field_name='id')
    cost=forms.IntegerField()
    stat=(('Pending','Pending'),('Approved','Approved'),('Released','Released'))
    status=forms.ChoiceField( choices=stat)

class UpdateCostForm(forms.Form):
    cost=forms.IntegerField()

class MechanicAcceptStatusForm(forms.Form):
    mechanic_location = forms.CharField(max_length=255)
    mechanic_mobile = forms.CharField(max_length=15)

class MechanicUpdateStatusForm(forms.Form):
    cost = forms.CharField(max_length=255)
    
class managerAcceptStatusForm(forms.Form):
    mechanic_location = forms.CharField(max_length=255)
    mechanic_mobile = forms.CharField(max_length=15)

class managerUpdateStatusForm(forms.Form):
    cost = forms.CharField(max_length=255)
    
  
class FeedbackForm(forms.ModelForm):
    class Meta:
        model=models.Feedback
        fields=['by','message']
        widgets = {
        'message':forms.Textarea(attrs={'rows': 6, 'cols': 30})
        }

#for Attendance related form
presence_choices=(('Present','Present'),('Absent','Absent'))
class AttendanceForm(forms.Form):
    present_status=forms.ChoiceField( choices=presence_choices)
    date=forms.DateField()

class AskDateForm(forms.Form):
    date=forms.DateField()


#for contact us page
class ContactusForm(forms.Form):
    Name = forms.CharField(max_length=30)
    Email = forms.EmailField()
    Message = forms.CharField(max_length=500,widget=forms.Textarea(attrs={'rows': 3, 'cols': 30}))
