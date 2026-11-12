from django.contrib import admin
from .models import Driver, Mechanic, Manager, Attendance, DriverNotification, Feedback, Request, MechanicNotification, MechanicWithdrawalHistory, DriverFundHistory, ManagerWithdrawalHistory

# Register your models here.

admin.site.register(Driver)
admin.site.register(Mechanic)
admin.site.register(Attendance)
admin.site.register(DriverNotification)
admin.site.register(Feedback)
admin.site.register(Request)
admin.site.register(MechanicNotification)
admin.site.register(MechanicWithdrawalHistory)
admin.site.register(Manager)
admin.site.register(DriverFundHistory)
admin.site.register(ManagerWithdrawalHistory)