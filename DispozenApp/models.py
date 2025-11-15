from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.utils import timezone
# Create your models here.
ROLE_CHOICES = [
    ('admin', 'Admin'),
    ('super_admin', 'Super Admin'),
    ('partner', 'Partner'),
    ('organizer', 'Organizer'),
]
class DispozenUser(AbstractUser):
    fb_id=models.CharField(max_length=50,blank=True,null=True,unique=True) #Partner and Organizer must have fb id but admin and super admin don't need it
    username = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    name=models.CharField(max_length=100,blank=True,null=True)
    email=models.EmailField(max_length=100,unique=True)
    phone=models.CharField(max_length=20)
    location=models.CharField(max_length=100,blank=True,null=True)
    role=models.CharField(max_length=20,choices=ROLE_CHOICES)
    profile_picture=models.ImageField(upload_to='profile_pictures/',blank=True,null=True)
    is_verified=models.BooleanField(default=False)
    partner_rating=models.FloatField(default=0.0,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    portfolio_website=models.URLField(max_length=200,blank=True,null=True)
    service_types=models.CharField(max_length=200,blank=True,null=True)
    description=models.TextField(blank=True,null=True)
    otp=models.CharField(max_length=6,blank=True,null=True)
    otp_created_at=models.DateTimeField(blank=True,null=True)
    
    

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='dispozenuser_set',  
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='dispozenuser_permissions_set',  
        blank=True,
    )

    def __str__(self):
        return self.email

class EventModel(models.Model):
    organizer_id=models.ForeignKey(DispozenUser,on_delete=models.CASCADE)
    partner_name=models.ForeignKey(DispozenUser,on_delete=models.CASCADE,related_name='partner_events',blank=True,null=True)
    event_name=models.CharField(max_length=100)
    event_description=models.TextField(max_length=1000,blank=True,null=True) 
    event_category=models.CharField(max_length=50,blank=True,null=True)
    location=models.CharField(max_length=100,blank=True,null=True)
    schedule1_date=models.CharField(max_length=100,blank=True,null=True)
    schedule1_date_time=models.CharField(max_length=100,blank=True,null=True)
    schedule1_going=models.IntegerField(default=0)
    schedule1_not_going=models.IntegerField(default=0)
    schedule1_maybe=models.IntegerField(default=0)
    schedule2_date=models.CharField(max_length=100,blank=True,null=True)
    schedule2_date_time=models.CharField(max_length=100,blank=True,null=True)
    schedule2_going=models.IntegerField(default=0)
    schedule2_not_going=models.IntegerField(default=0)
    schedule2_maybe=models.IntegerField(default=0)
    schedule_date=models.CharField(max_length=100,blank=True,null=True)
    schedule_date_time=models.CharField(max_length=100,blank=True,null=True)
    organizer_name=models.CharField(max_length=50,blank=True,null=True)
    conformation=models.BooleanField(default=False)
    has_accepted=models.BooleanField(default=False)
    confirm_schedule=models.CharField(max_length=100,blank=True,null=True)
    going=models.IntegerField(default=0)
    not_going=models.IntegerField(default=0)
    maybe=models.IntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)

class PartnerSuccessfulEvent(models.Model):
    partner_id=models.ForeignKey(DispozenUser,on_delete=models.CASCADE,related_name='successful_events')
    event_id=models.OneToOneField(EventModel,on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)

class OrganizerSendRequestToPartner(models.Model):
    organizer_id=models.ForeignKey(DispozenUser,on_delete=models.CASCADE,related_name='organizer_requests')
    partner_id=models.ForeignKey(DispozenUser,on_delete=models.CASCADE,related_name='partner_requests')
    event_id=models.ForeignKey(EventModel,on_delete=models.CASCADE)
    message=models.TextField(max_length=1000,blank=True,null=True)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at=models.DateTimeField(auto_now_add=True)


class InvitedGuests(models.Model):
    event_id=models.ForeignKey(EventModel,on_delete=models.CASCADE)
    guest_name=models.CharField(max_length=100,blank=True,null=True)
    guest_email=models.EmailField(max_length=100)
    invited_at=models.DateTimeField(auto_now_add=True)

class PaymentModel(models.Model):
    user_id=models.ForeignKey(DispozenUser,on_delete=models.CASCADE)
    package=models.CharField(max_length=100)
    amount=models.FloatField()
    payment_date=models.DateTimeField(auto_now_add=True)
    payment_method=models.CharField(max_length=50,blank=True,null=True)
    
    status=models.BooleanField(max_length=50,blank=True,null=True,default=False)

class Notification(models.Model):
    partner = models.ForeignKey('DispozenUser', on_delete=models.CASCADE, related_name='notifications')  
    organizer = models.ForeignKey('DispozenUser', on_delete=models.CASCADE)  
    event = models.ForeignKey('EventModel', on_delete=models.CASCADE)  
    title = models.CharField(max_length=255)  
    content = models.TextField()  
    notification_type = models.CharField(max_length=50)  
    is_read = models.BooleanField(default=False)  
    created_at = models.DateTimeField(default=timezone.now)  

    def __str__(self):
        return f"Notification for {self.partner.name} from {self.organizer.name}"
    

class GuestEmail(models.Model):
    eventId=models.ForeignKey(EventModel, on_delete=models.CASCADE)
    email=models.EmailField()


class SelectedPlace(models.Model):
    organizer=models.ForeignKey(DispozenUser,on_delete=models.CASCADE,related_name='selected_places')
    name = models.CharField(max_length=255)
    address = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    category = models.CharField(max_length=100, blank=True, null=True)
    sub_category = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    selected_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'selected_places'
        ordering = ['-selected_at']
    
    def __str__(self):
        return f"{self.name} - {self.location}"