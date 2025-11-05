
from .models import EventModel, GuestEmail
from django.core.mail import send_mail
from django.conf import settings

def send_event_email(event_id, subject, message):

    guest_emails = GuestEmail.objects.filter(eventId=event_id)

    email_list = [guest.email for guest in guest_emails]

    if email_list:

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,  
            email_list,                   
            fail_silently=False,          
        )
        return True
    else:
        return False
