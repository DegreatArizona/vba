from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cloudinary.models import CloudinaryField
from datetime import date, timedelta
from django.utils.timezone import localtime
##################################
#             Mechanic           #
##################################

class Mechanic(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    my_manager = models.ForeignKey('Manager', on_delete=models.CASCADE, null=True, blank=True, related_name='mechanics_under')
    profile_pic = CloudinaryField('profile picture', null=True, blank=True)
    business_license =  CloudinaryField('mechanic License', null=True, blank=True)
    service = models.TextField(null=True, blank=True)
    salary = models.PositiveIntegerField(null=True, blank=True, default=0)
    charge = models.PositiveBigIntegerField(null=True, blank=True, default=5,)
    status = models.BooleanField(default=False)
    address = models.CharField(max_length=150, null=True, blank=True)
    union_name = models.CharField(max_length=150, null=True, blank=True)
    union_location = models.CharField(max_length=150, null=True, blank=True)
    mobile = models.CharField(max_length=150, null=True, blank=True)
    account_number = models.CharField(max_length=20, blank=True)
    bank_code = models.CharField(max_length=10, blank=True)
    bank_name = models.CharField(max_length=100, null=False, default="Select Bank")
    account_name = models.CharField(max_length=200, blank=True)
    currency = models.CharField(max_length=40, null=False, default="NGN")
    state = models.CharField(max_length=100, blank=True)
    local_government = models.CharField(max_length=100, blank=True)
    rating = models.FloatField(default=0.0)
    is_pro = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    subscription_expiration_date = models.DateField(null=True, blank=True, default=date.today() + timedelta(days=30))

    @property
    def get_name(self):
        return self.user.first_name + " " + self.user.last_name
    @property
    def get_id(self):
        return self.user.id
    def __str__(self):
        return f"({self.user.id}) - {self.user.username} - {self.user.first_name+ ' ' +self.user.last_name}"

class MechanicWithdrawalHistory(models.Model):
    account_number = models.CharField(max_length=20, blank=True)
    bank_code = models.CharField(max_length=10, blank=True)
    bank_name = models.CharField(max_length=100, default="Select Bank Name")
    narration = models.TextField(max_length=500, blank=True)
    mechanic = models.ForeignKey('Mechanic', on_delete=models.CASCADE, null=True, blank=True)
    transaction_reference = models.CharField(max_length=40, unique=True)
    currency = models.CharField(max_length=10, default="NGN")
    amount_recieved = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=0)
    amount_withdraw = models.PositiveBigIntegerField(null=True, blank=True, default=0,)
    account_name = models.CharField(max_length=200, blank=True)
    STATUS_CHOICES = [
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Pending', 'Pending'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', null=True)
    date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return (
            f"ID: ({self.id}) Mechanic: {self.mechanic.user.username} "
            f"- Ref: ({self.transaction_reference}) - Status: {self.status} - {self.date.strftime('%Y-%m-%d %H:%M:%S')}"
        )

class MechanicNotification(models.Model):
    mechanic = models.ForeignKey('Mechanic', on_delete=models.CASCADE, related_name="mechnotifications")
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.mechanic.get_name} - {self.message[:50]} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

##################################
#             Manager              #
##################################
class Manager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mechanics = models.ManyToManyField('Mechanic', blank=True, related_name='managers')
    profile_pic = CloudinaryField('profile picture', null=True, blank=True)
    business = models.CharField(max_length=150, null=True, blank=True)
    salary = models.PositiveIntegerField(null=True, blank=True, default=0)
    charge = models.PositiveBigIntegerField(null=True, blank=True, default=5,)
    status = models.BooleanField(default=False)
    address = models.CharField(max_length=150, null=True,)
    mobile = models.CharField(max_length=150, null=True,)
    GENDER_CHOICE =[('Male', 'Male'), ('Female', 'Female')]
    gender = models.CharField(max_length=150, choices=GENDER_CHOICE, null=True,)
    account_number = models.CharField(max_length=20, blank=True)
    bank_code = models.CharField(max_length=10, blank=True)
    bank_name = models.CharField(max_length=100, null=False, default="Select Bank")
    account_name = models.CharField(max_length=200, blank=True)
    currency = models.CharField(max_length=40, null=False, default="NGN")
    state = models.CharField(max_length=100,)
    local_government = models.CharField(max_length=100,)
    rating = models.FloatField(default=0.0)
    is_pro = models.BooleanField(default=False)
    guarantor_name = models.CharField(max_length=150, null=True)
    guarantor_mobile = models.CharField(max_length=150, null=True)
    guarantor_email = models.CharField(max_length=150, null=True)
    guarantor_pic = CloudinaryField('profile picture', null=True, blank=True)
    guarantor2_name = models.CharField(max_length=150, null=True)
    guarantor2_mobile = models.CharField(max_length=150, null=True)
    guarantor2_email = models.CharField(max_length=150, null=True)
    guarantor2_pic = CloudinaryField('profile picture', null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    subscription_expiration_date = models.DateField(null=True, blank=True, default=date.today() + timedelta(days=30))

    @property
    def get_name(self):
        return self.user.first_name + " " + self.user.last_name
    @property
    def get_id(self):
        return self.user.id
    def __str__(self):
        return f"({self.user.id}) - {self.user.username} - {self.user.first_name+ ' ' +self.user.last_name}"
    
class ManagerWithdrawalHistory(models.Model):
    account_number = models.CharField(max_length=20, blank=True)
    bank_code = models.CharField(max_length=10, blank=True)
    bank_name = models.CharField(max_length=100, default="Select Bank Name")
    narration = models.TextField(max_length=500, blank=True)
    manager = models.ForeignKey('Manager', on_delete=models.CASCADE, null=True, blank=True)
    transaction_reference = models.CharField(max_length=40, unique=True)
    currency = models.CharField(max_length=10, default="NGN")
    amount_recieved = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=0)
    amount_withdraw = models.PositiveBigIntegerField(null=True, blank=True, default=0,)
    account_name = models.CharField(max_length=200, blank=True)
    STATUS_CHOICES = [
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Pending', 'Pending'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', null=True)
    date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return (
            f"ID: ({self.id}) Manager: {self.manager.user.username} "
            f"- Ref: ({self.transaction_reference}) - Status: {self.status} - {self.date.strftime('%Y-%m-%d %H:%M:%S')}"
        )

class ManagerNotification(models.Model):
    manager = models.ForeignKey('Manager', on_delete=models.CASCADE, related_name="mannotifications")
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.manager.get_name} - {self.message[:50]} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
##################################
#             Driver             #
##################################

class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    profile_pic = CloudinaryField('profile picture', null=True, blank=True)
    address = models.CharField(max_length=150, null=True, blank=True)
    balance = models.PositiveIntegerField(null=True, blank=True, default=0)
    virtual_account_number = models.CharField(max_length=20, blank=True, null=True)
    bank_name = models.CharField(max_length=20, blank=True, null=True)
    mobile = models.CharField(max_length=150, null=True, blank=True)
    license_no = models.CharField(max_length=150, null=True, blank=True)
    vehicle_model = models.CharField(max_length=150, null=True, blank=True)
    is_pro = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    subscription_expiration_date = models.DateField(null=True, blank=True, default=date.today() + timedelta(days=30))

    @property
    def get_name(self):
        return self.user.first_name + " " + self.user.last_name

    def get_instance(self):
        return self

    def __str__(self):
        return f"({self.user.id}) - {self.user.username} - {self.user.first_name+ ' ' +self.user.last_name}"

class DriverNotification(models.Model):
    driver = models.ForeignKey('Driver', on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.driver.get_name} - {self.message[:50]} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

class DriverFundHistory(models.Model):
    narration = models.TextField(max_length=500, blank=True)
    driver = models.ForeignKey('Driver', on_delete=models.CASCADE, null=True, blank=True)
    transaction_reference = models.CharField(max_length=40, unique=True)
    currency = models.CharField(max_length=10, default="NGN")
    amount_recieved = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=0)
    charges = models.PositiveBigIntegerField(null=True, blank=True, default=0,)
    STATUS_CHOICES = [
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Pending', 'Pending'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', null=True)
    date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return (
            f"ID: ({self.id}) Driver: {self.driver.user.username} "
            f"- Ref: ({self.transaction_reference}) - Status: {self.status} - {self.date.strftime('%Y-%m-%d %H:%M:%S')}"
        )


##################################
#             General            #
##################################

class Request(models.Model):
    cat = (('Tire Repair','Tire Repair'),('Towing Service','Towing Service'),('Battery Jumpstart','Battery Jumpstart'),('Electrical Issues','Electrical Issues'),('Engine Repair', 'Engine Repair'), ('Bodywork/Collision Repair', 'Bodywork/Collision Repair'), ('Other Service', 'Other Service'))
    category = models.CharField(max_length = 150, choices=cat)

    vehicle_no = models.CharField(max_length=150, null=False)
    vehicle_name = models.CharField(max_length=140, null=False)

    location = models.CharField(max_length=255, null=False)
    mechanic_location = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)

    mobile = models.CharField(max_length=40, null=False, default="Unknown")
    mechanic_mobile = models.CharField(max_length=40, null=True, blank=True)
    
    latitude = models.FloatField(null=True, blank=True, default=6.5244)
    longitude = models.FloatField(null=True, blank=True, default=3.3792)

    eta = models.CharField(max_length=50, null=False, blank=True, default="Not Available")

    problem_description = models.TextField(max_length=500, null=False)
    date = models.DateTimeField(auto_now_add=True)
    estimated_completion_date = models.DateTimeField(null=True, blank=True)

    currency = models.CharField(max_length=40, null=False, default="NGN")
    cost = models.PositiveBigIntegerField(null=True, blank=True, default=0,)
    tax = models.PositiveBigIntegerField(null=True, default=10,)

    transaction_reference = models.CharField(max_length=40, null=False, default="TXN0-0000000")

    manager = models.ForeignKey('Manager', on_delete=models.CASCADE, null=True, blank=True)
    mechanic = models.ForeignKey('Mechanic', on_delete=models.CASCADE, null=True, blank=True)
    driver = models.ForeignKey('Driver', on_delete=models.CASCADE, null=True)
    
    mth = (('Card', 'Card'), ('Balance', 'Balance'), ('Card/Balance', 'Card/Balance'))
    method = models.CharField(max_length=50,choices=mth, default='Card/Balance',null=True,)

    inv = (('Paid', 'Paid'), ('Pending', 'Pending'), ('Cancelled', 'Cancelled'))
    invoice = models.CharField(max_length=50,choices=inv,default='Pending',null=True,)

    stat=(('Pending','Pending'),('Approved','Approved'),('Accepted','Accepted'),('Repairing', 'Repairing'),('Done','Done'),('Released', 'Released'),('Cancelled','Cancelled'))
    status=models.CharField(max_length=50,choices=stat,default='Pending',null=True)
    current_date = localtime(timezone.now())
    current_year = current_date.year


    def __str__(self):
        return f"Driver: {self.driver} Request {self.id}: {self.vehicle_name} ({self.status})"
    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['date']),
        ]


class Attendance(models.Model):
    mechanic=models.ForeignKey('Mechanic',on_delete=models.CASCADE,null=True)
    date=models.DateField()
    present_status = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.mechanic.get_name} {self.present_status}"

class Feedback(models.Model):
    date=models.DateField(auto_now=True)
    by=models.CharField(max_length=40)
    message=models.CharField(max_length=500)

    def __str__(self):
        return self.by +" "+ self.message
