from django.contrib.admin.options import model_format_dict
from rest_framework import serializers
from .models import DispozenUser,EventModel,PartnerSuccessfulEvent,OrganizerSendRequestToPartner,PaymentModel
from .pagination import CustomPageNumberPagination

class DispozenUpdateProfileInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model=DispozenUser
        fields=['name','phone','profile_picture']

class UpdateAdminProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = DispozenUser
        fields = ['id','name', 'email', 'phone', 'role']
    def validate(self, data):
        if 'password' in data:
            password = data.pop('password')
            self.instance.set_password(password)
            self.instance.save()
        return data

class DispozenUserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = DispozenUser
        fields = ['id', 'name', 'email', 'phone', 'location', 'role', 'created_at', 'fb_id', 'profile_picture']

class ConfirmEventSerializerPartnerName(serializers.ModelSerializer):
    class Meta:
        model = DispozenUser
        fields = ['name']

class ConfirmEventSerializer(serializers.ModelSerializer):
    partner_name = ConfirmEventSerializerPartnerName(read_only=True)

    class Meta:
        model = EventModel
        fields = [
            'id',
            'event_name',
            'event_description',
            'confirm_schedule',
            'location',
            'going',
            'not_going',
            'maybe',
            'partner_name',  # partner_name will now be properly serialized
        ]

    

class InitialConfirmEventSerializer(serializers.ModelSerializer):

    class Meta:
        model = EventModel
        fields = [
            'id',
            'event_name',
            'event_description',
            'confirm_schedule',
            'location',
            'going',
            'not_going',
            'maybe',
        ]    
class AllEventSerializer(serializers.ModelSerializer):

    class Meta:
        model = EventModel
        fields = [
            'id',
            'event_name',
            'event_description',
            'location',
            'schedule1_date',
            'schedule1_going',
            'schedule1_not_going',
            'schedule1_maybe',
            'schedule2_date',
            'schedule2_going',
            'schedule2_not_going',
            'schedule2_maybe',
            
        ] 

class OrganizerSelectPartnerSerializer(serializers.ModelSerializer):
    partner_details = serializers.SerializerMethodField()

    class Meta:
        model = OrganizerSendRequestToPartner
        fields = ['partner_details']

    def get_partner_details(self, obj):
        partner = obj.partner_id
        event=obj.event_id
        return {
            'partner_id': partner.id,
            'event_id': event.id,
            'name': partner.name,
            'role': partner.role,
            
            
        }

class PartnerListSerializer(serializers.ModelSerializer):
    total_events = serializers.SerializerMethodField()
    class Meta:
        model = DispozenUser
        fields = ['id', 'name', 'email', 'phone','partner_rating','total_events']
    def get_total_events(self, obj):
        
        return obj.successful_events.count()

class PartnerSuccessfulEventSerializer(serializers.ModelSerializer):
    event_details = serializers.SerializerMethodField()
    class Meta:
        model = PartnerSuccessfulEvent
        fields = ['event_details']
    def get_event_details(self, obj):
        event = obj.event_id
        return {
            'id': event.id,
            'event_name': event.event_name,
            'event_description': event.event_description,
            'location': event.location,
            'confirm_schedule': event.confirm_schedule,
            # 'schedule_date_time': event.schedule_date_time,
            'going': event.going,
            'not_going': event.not_going,
            'maybe': event.maybe,
        }
class PaymentModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentModel
        fields = ['package','payment_date','amount']

class CreateEventModelSerializer(serializers.ModelSerializer):
    # organizer_id = serializers.CharField(write_only=True)
    organizer_id = serializers.PrimaryKeyRelatedField(
        queryset=DispozenUser.objects.all(),
        write_only=True
    )
    class Meta:
        model = EventModel
        fields = [
            'organizer_id',
            'event_name',
            'event_description',
            'event_category',
            'location',
            'schedule1_date',
            'schedule2_date',
            'organizer_name',
            'conformation',
            'going',
            'not_going',
            'maybe',
            
        ]

class OrganizerPartnerProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispozenUser
        fields = ['id','name', 'phone', 'location', 'portfolio_website','service_types','description']

class DispozenPartnerSerializer(serializers.ModelSerializer):
    successful_events = PartnerSuccessfulEventSerializer(many=True, read_only=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = DispozenUser
        fields = ['id', 'name', 'email', 'phone', 'role', 'created_at', 'fb_id', 'partner_rating','successful_events', 'profile_picture']
        


#Authentication Serializer for Registration
class DispozenAdminCreateSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True)
    class Meta:
        model=DispozenUser
        fields = ['name', 'email', 'phone', 'password', 'role']
    def create(self, validated_data):
        user = DispozenUser(
            name=validated_data['name'],
            email=validated_data['email'],
            phone=validated_data['phone'],
            role=validated_data['role'],
           
            
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
class DispozenUserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = DispozenUser
        fields = ['name', 'email', 'phone', 'location', 'role', 'password', 'confirm_password', 'fb_id']
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords must match.")
        if data['role']=='partner' or data['role']=='organizer':
            if not data.get('fb_id'):
                raise serializers.ValidationError("fb_id is required for partners and organizers.")
        return data

    def create(self, validated_data):
        user = DispozenUser(
            name=validated_data['name'],
            email=validated_data['email'],
            phone=validated_data['phone'],
            location=validated_data.get('location', None),
            role=validated_data['role'],
            fb_id=validated_data.get('fb_id', None),
        )
        user.set_password(validated_data['password'])
        user.save()
        return user



    
    def validate_organizer_id(self, value):
        """
        Validate that the organizer exists with the given fb_id
        """
        try:
            organizer = DispozenUser.objects.get(fb_id=value)
            return organizer
        except DispozenUser.DoesNotExist:
            raise serializers.ValidationError(
                f"Organizer with fb_id '{value}' does not exist."
            )
    
class EventDetailsOrganizerSendRequestSerializer(serializers.ModelSerializer):
    totalevents=serializers.SerializerMethodField()
    class Meta:
        model = EventModel
        fields = [
            'event_name',
            'event_description',
            'going',
            'confirm_schedule',
            # 'schedule_date_time',
            'totalevents',
            
        ]
    def get_totalevents(self, obj):
        total_events=EventModel.objects.filter(organizer_id=obj.organizer_id,has_accepted=True).count()
        return total_events
    
class RequestEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizerSendRequestToPartner
        fields = ['event_id', 'organizer_id', 'partner_id','message']
        

class OrganizerSendRequestToPartnerSerializer(serializers.ModelSerializer):
    event_details = EventDetailsOrganizerSendRequestSerializer(source='event_id', read_only=True)
    organizerinfo = serializers.SerializerMethodField()

    class Meta:
        model = OrganizerSendRequestToPartner
        fields = ['event_id', 'event_details', 'organizer_id', 'organizerinfo']

    def get_organizerinfo(self, obj):
        organizer = obj.organizer_id  # Ensure you get the related organizer object
        return {
            'name': organizer.name,
            'email': organizer.email,
            'phone': organizer.phone,
        }

class OrganizerEventShowtoPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventModel
        fields = [
            'id',
            'event_name',
            'event_description',
            'schedule_date',
            'going',
            
        ]



class GuestVotingSerializer(serializers.Serializer):
    event_id=serializers.IntegerField()
    email=serializers.EmailField()
    vote=serializers.IntegerField()
    schedule=serializers.IntegerField()
    
class DateTimeModificationSerializer(serializers.Serializer):
    date_time=serializers.CharField(max_length=100)
    iso_code=serializers.CharField(max_length=10)



class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentModel
        fields = [
            'id', 'user_id', 'package', 'amount', 'payment_date', 
            'payment_method', 'stripe_payment_intent_id', 
            'payment_status', 'currency', 'description'
        ]
        read_only_fields = ['id', 'payment_date', 'stripe_payment_intent_id', 'payment_status']

class CreatePaymentIntentSerializer(serializers.Serializer):
    amount = serializers.FloatField(required=True)
    package = serializers.CharField(required=True, max_length=100)
    currency = serializers.CharField(default='usd', max_length=3)
    description = serializers.CharField(required=False, allow_blank=True)
    user_fb_id = serializers.CharField(required=True)