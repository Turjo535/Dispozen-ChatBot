from django.contrib import admin
from .models import DispozenUser, EventModel, PartnerSuccessfulEvent,OrganizerSendRequestToPartner,PaymentModel,Notification
# Register your models here.
class DispozenUserAdmin(admin.ModelAdmin):
    model = DispozenUser

    list_display = [field.name for field in DispozenUser._meta.fields if field.name not in ['last_login', 'is_superuser', 'first_name', 'last_name', 'is_staff', 'password']]

    verbose_name = 'Dispozen User'
    verbose_name_plural = 'Dispozen Users'

class EventModelAdmin(admin.ModelAdmin):
    model = EventModel
    list_display = [field.name for field in EventModel._meta.fields]

class PartnerSuccessfulEventAdmin(admin.ModelAdmin):
    model = PartnerSuccessfulEvent
    list_display = [field.name for field in PartnerSuccessfulEvent._meta.fields]
class OrganizerSendRequestToPartnerAdmin(admin.ModelAdmin):
    model = OrganizerSendRequestToPartner
    list_display = [field.name for field in OrganizerSendRequestToPartner._meta.fields]
class PaymentModelAdmin(admin.ModelAdmin):
    model = PaymentModel
    list_display = [field.name for field in PaymentModel._meta.fields]

class NotificationAdmin(admin.ModelAdmin):
    model = Notification
    list_display = [field.name for field in Notification._meta.fields]
admin.site.register(PartnerSuccessfulEvent,PartnerSuccessfulEventAdmin)
admin.site.register(OrganizerSendRequestToPartner,OrganizerSendRequestToPartnerAdmin)   
admin.site.register(EventModel,EventModelAdmin)
admin.site.register(DispozenUser,DispozenUserAdmin)
admin.site.register(PaymentModel,PaymentModelAdmin)
admin.site.register(Notification,NotificationAdmin)