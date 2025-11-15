# from django.shortcuts import render
import urllib.parse
import urllib.request
import json
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import models
from datetime import datetime
from datetime import timedelta
import pytz  
from decouple import config
from .serializers import DispozenUserRegistrationSerializer,DispozenUserSerializer, DateTimeModificationSerializer, CreateEventModelSerializer,DispozenAdminCreateSerializer,PartnerListSerializer,PaymentModelSerializer,OrganizerPartnerProfileUpdateSerializer,RequestEventSerializer,UpdateAdminProfileSerializer
from .serializers import PartnerSuccessfulEventSerializer,OrganizerSendRequestToPartnerSerializer,DispozenPartnerSerializer,DispozenUpdateProfileInformationSerializer,ConfirmEventSerializer,InitialConfirmEventSerializer,AllEventSerializer,OrganizerSelectPartnerSerializer,OrganizerEventShowtoPartnerSerializer,GuestVotingSerializer
from .models import DispozenUser, EventModel,PartnerSuccessfulEvent,OrganizerSendRequestToPartner,PaymentModel,Notification,GuestEmail
from .countrytime import convert_utc_to_local
from datetime import time
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .googlemaps import geocode_location
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .permission import IsSuperAdminUser, IsAdminUser, IsPartnerUser, IsOrganizerUser
from .pagination import CustomPageNumberPagination
from django.contrib.auth import authenticate
from django.core.mail import send_mail
import secrets, string
from django.conf import settings
from .email import send_event_email

def get_tokens_for_user(user):
    if not user.is_active:
      raise AuthenticationFailed("User is not active")

    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }



# Auth Views

class DispozenUserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]  # No authentication needed for registration

    def post(self, request):
        serializer = DispozenUserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            print(serializer.data)
            digits = string.digits  
            otp = ''.join(secrets.choice(digits) for _ in range(6))
            user.otp=otp
            user.otp_created_at=datetime.now(pytz.utc)
            user.save()
            print(otp)
            send_mail(
                subject="Dispozen account Verification",
                message=f"Your OTP for email verification is: {otp}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return Response(
                {"message": "User created successfully.Check your given email for otp","user": DispozenUserSerializer(user).data},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class SendOTPView(APIView):
    permission_classes = [permissions.AllowAny]  

    def post(self, request):
        email = request.data.get('email')
        try:
            user = DispozenUser.objects.get(email=email)
        except DispozenUser.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

        digits = string.digits  
        otp = ''.join(secrets.choice(digits) for _ in range(6))
        user.otp=otp
        user.otp_created_at=datetime.now(pytz.utc)
        user.save()
        print(otp)
        send_mail(
            subject="Dispozen account Verification - Resend OTP",
            message=f"Your OTP for email verification is: {otp}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return Response(
            {"message": "OTP resent successfully. Check your email."},
            status=status.HTTP_200_OK,
        )
class OTPVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        try:
            user = DispozenUser.objects.get(email=email)
        except DispozenUser.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

        if user.otp == otp and datetime.now(pytz.utc) - user.otp_created_at <= timedelta(minutes=5):
            user.is_verified = True
            user.otp=None
            user.otp_created_at=None
            user.save()
            token=get_tokens_for_user(user)
            return Response({"message": "Email verified successfully.","Tokens":token}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid OTP or you are running out of time."}, status=status.HTTP_400_BAD_REQUEST)
        
class DispozenUserLoginView(APIView):
    permission_classes = [permissions.AllowAny]  # No authentication needed for login

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            user_obj = DispozenUser.objects.get(email=email)
        except DispozenUser.DoesNotExist:
            
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        
        if not user_obj.check_password(password): 
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        user = authenticate(request, username=user_obj.username, password=password) 
        if user:
            serializer = DispozenUserSerializer(user) 
        token = get_tokens_for_user(user)
        return Response({"message": "Login successful", "user": serializer.data, "tokens": token}, status=status.HTTP_200_OK)
    

class DispozenUserChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        # email=request.data.get('email')
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        retype_password = request.data.get('retype_password')

        if not user.check_password(old_password):
            return Response({"error": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        if new_password != retype_password:
            return Response({"error": "New password and retype password do not match."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)

class DispozenAdminAccountSettingProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = DispozenUpdateProfileInformationSerializer(user, data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile information updated successfully.", "user": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class DispozenUserDisableAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated|IsSuperAdminUser|IsAdminUser]
    def get(self, request,id):
        user = DispozenUser.objects.get(id=id)
        if user.is_verified==False:
            return Response({"message": "Account is already disabled."}, status=status.HTTP_400_BAD_REQUEST)
        user.is_verified = False
        user.save()
        return Response({"message": "Account disabled successfully."}, status=status.HTTP_200_OK)
# class DispozenUserEnableAccountView(APIView):
#     permission_classes = [permissions.IsAuthenticated|IsSuperAdminUser|IsAdminUser]
#     def post(self, request):
#         user = request.user
#         user.is_verified = True
#         user.save()
#         return Response({"message": "Account enabled successfully."}, status=status.HTTP_200_OK)

class DispozenUserForgotPasswordResetView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        
        if new_password != confirm_password:
            return Response({"error": "New password and confirm password do not match."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


#Dispozen Admin Dashboard Website 
#Admin Info View   

class SuperAdminCreateAccountView(APIView):
    permission_classes = [IsSuperAdminUser]
    def post(self, request):
        
        serializer = DispozenAdminCreateSerializer(data=request.data)
        role = request.data.get('role', '').lower()
        if role not in ['admin', 'super_admin']:
            return Response({"error": "Super admin can only create admin or super admin accounts."}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class admininfo(APIView):
    permission_classes = [IsSuperAdminUser | IsAdminUser]
    def get(self, request):
        admin = request.user
        serializer = DispozenUserSerializer(admin)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DispozenAdminUpdateProfileView(APIView):
    permission_classes = [IsSuperAdminUser | IsAdminUser]

    def put(self, request):
        admin = request.user
        serializer = UpdateAdminProfileSerializer(admin, data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save() 
            return Response({"message": "Profile information updated successfully.", "admin": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DispozenAdminListView(APIView):
    permission_classes = [IsSuperAdminUser | IsAdminUser]

    def get(self, request):
        admin = DispozenUser.objects.filter(role__in=['admin', 'super_admin'])
        serializer = DispozenUserSerializer(admin, many=True)
        admin_data = [
            {
                'id': a.id,
                "name": a.name,
                "email": a.email,
                "phone": a.phone,
                "location": a.location,
                "role": a.role,
            }
            for a in admin
        ]
        return Response(admin_data, status=status.HTTP_200_OK)

class Delete_User(APIView):
    permission_classes = [permissions.IsAuthenticated|IsSuperAdminUser|IsAdminUser]

    def delete(self, request, id):
        try:
            admin_user = DispozenUser.objects.get(id=id)
            if admin_user.role == 'super_admin' and request.user.role != 'admin':
                return Response({"error": "Super admin can only delete admin accounts."}, status=status.HTTP_400_BAD_REQUEST)
            admin_user.delete()
            return Response({"message": "user deleted successfully."}, status=status.HTTP_200_OK)
        except DispozenUser.DoesNotExist:
            return Response({"error": "user not found."}, status=status.HTTP_404_NOT_FOUND)

class DispozenOrganizerListView(APIView):
    permission_classes = [IsSuperAdminUser | IsAdminUser]

    def get(self, request):
        
        organizers = DispozenUser.objects.filter(role='organizer')
        serializer = DispozenUserSerializer(organizers, many=True)
        
        organizer_data = [
            {
                'id': o.id,
                "name": o.name,
                "email": o.email,
                "phone": o.phone,
                "location": o.location,
            }
            for o in organizers
        ]
        return Response(organizer_data, status=status.HTTP_200_OK)

class DispozenPartnerListView(APIView):
    permission_classes = [IsSuperAdminUser | IsAdminUser]

    def get(self, request):
        partners = DispozenUser.objects.filter(role='partner')
        serializer = DispozenUserSerializer(partners, many=True)
        partner_data = [
            {
                'id': p.id,
                "name": p.name,
                "email": p.email,
                "phone": p.phone,
                "location": p.location,
            }
            for p in partners
        ]
        return Response(partner_data, status=status.HTTP_200_OK)
    

class DispozenUsersOverView(APIView):
    permission_classes = [IsSuperAdminUser | IsAdminUser]

    def get(self, request):
        organizer_count = DispozenUser.objects.filter(role='organizer').count()
        partner_count = DispozenUser.objects.filter(role='partner').count()
        total_users = organizer_count + partner_count
        today_new_users = DispozenUser.objects.filter(created_at__date=datetime.now().date()).count()
        total_subscribers = PaymentModel.objects.count()
        total_earned = PaymentModel.objects.filter(status=True).aggregate(total=models.Sum('amount'))['total'] or 0.0

        data = {
            "total_users": total_users,
            "today_new_users": today_new_users,
            "total_subscribers": total_subscribers,
            "total_earned": total_earned,
        }
        return Response(data, status=status.HTTP_200_OK)

# class AdminDeleteOrganizerPartnerView(APIView):
#     permission_classes = [IsSuperAdminUser | IsAdminUser]

#     def delete(self, request, id):
#         try:
#             user = DispozenUser.objects.get(id=id, role__in=['organizer', 'partner'])
#             user.delete()
#             return Response({"message": "User deleted successfully."}, status=status.HTTP_200_OK)
#         except DispozenUser.DoesNotExist:
#             return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
# class AdminOrganizerEventView(APIView):
#     permission_classes = [IsSuperAdminUser | IsAdminUser]

#     def get(self, request, id):
#         try:
#             organizer = DispozenUser.objects.get(id=id, role='organizer')
#         except DispozenUser.DoesNotExist:
#             return Response({"error": "Organizer not found."}, status=status.HTTP_404_NOT_FOUND)

#         events = EventModel.objects.filter(organizer_id=organizer.id)
#         print(organizer.id)
#         serializer = CreateEventModelSerializer(events, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

# Organizer Dashboard Website 

class AllEventList(APIView):
    permission_classes = [IsOrganizerUser]

    def get(self, request):
        organizer = request.user
        events = EventModel.objects.filter(organizer_id=organizer.id, conformation=False,has_accepted=False)
        
        serializer = AllEventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class EventSchedulesConfirm(APIView):
    permission_classes = [IsOrganizerUser]
    def post(self, request, id):
        try:
            schedule=request.data.get('schedule')
            event = EventModel.objects.get(id=id)
            
        except EventModel.DoesNotExist:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
        if schedule=='schedule1':
            event.confirm_schedule=event.schedule1_date
            
            event.going=event.schedule1_going
            event.not_going=event.schedule1_not_going
            event.maybe=event.schedule1_maybe
        elif schedule=='schedule2':
            event.confirm_schedule=event.schedule2_date
            
            event.going=event.schedule2_going
            event.not_going=event.schedule2_not_going
            event.maybe=event.schedule2_maybe
        event.conformation=True
        event.save()
        serializer=InitialConfirmEventSerializer(event)
        return Response({"message": "Event confirm successfully.", "event": serializer.data}, status=status.HTTP_200_OK)


class InitialConfirmViewList(APIView):
    permission_classes = [IsOrganizerUser]

    def get(self, request):
        organizer = request.user
        events = EventModel.objects.filter(organizer_id=organizer.id, conformation=True,has_accepted=False)
        
        serializer = InitialConfirmEventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)    
    

class PartnerListView(APIView):
    permission_classes = [IsOrganizerUser]
    def get(self, request):
        print(request.user)
        partners = DispozenUser.objects.filter(role='partner')
        
        
        serializer = PartnerListSerializer(partners, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class PartnerSuccessfulEventView(APIView):
    permission_classes = [IsOrganizerUser]
    def get(self, request,id):
        events=PartnerSuccessfulEvent.objects.filter(partner_id=id)
        print(events)
        serializer = PartnerSuccessfulEventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class RequestEventView(APIView):
   
    
    def post(self, request):
        
        organizer = request.user
        
        
        partner_id = request.data.get('partner_id')
        event_id = request.data.get('event_id')

        
        try:
            partner = DispozenUser.objects.get(id=partner_id)
        except DispozenUser.DoesNotExist:
            return Response(
                {"detail": "Partner not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        
        try:
            event = EventModel.objects.get(id=event_id)
        except EventModel.DoesNotExist:
            return Response(
                {"detail": "Event not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        request_event=OrganizerSendRequestToPartner.objects.filter(partner_id=partner_id,event_id=event_id)
        
        if request_event.exists():
            return Response({"error":"You already sent request to this id."},status=status.HTTP_400_BAD_REQUEST)
        request_data = {
            'organizer_id': organizer.id,
            'partner_id': partner.id,
            'event_id': event.id,
            'message': 'Organizer sent request.',
            'status': 'pending',
        }
        
        serializer = RequestEventSerializer(data=request_data)
        if serializer.is_valid():
            organizer_request = serializer.save()

            # Create notification in database
            notification_data = {
                'partner': partner,
                'organizer': organizer,
                'event': event,
                'title': 'New Partnership Request',
                'content': f'{organizer.name} has sent you a request for an event.',
                'notification_type': 'request',
                'is_read': False,
            }
            notification = Notification.objects.create(**notification_data)

          
            channel_layer = get_channel_layer()
            
            
            notification_message = {
                "id": notification.id,
                "title": notification.title,
                "content": notification.content,
                "notification_type": notification.notification_type,
                "organizer_id": organizer.id,
                "organizer_name": organizer.name,
                "event_id": event.id,
                "event_name": event.name if hasattr(event, 'name') else None,
                "created_at": notification.created_at.isoformat() if hasattr(notification, 'created_at') else None,
                "is_read": False,
            }
            
            # Send to the partner's WebSocket group
            try:
                async_to_sync(channel_layer.group_send)(
                    f"user_{partner.id}",  # Target the partner's notification group
                    {
                        "type": "send_notification",  # Calls send_notification() in consumer
                        "message": notification_message,
                    }
                )
                print(f"✅ Notification sent to partner {partner.id} via WebSocket")
            except Exception as e:
                print(f"❌ Failed to send WebSocket notification: {str(e)}")
                

            return Response({
                "message": "Request sent successfully",
                
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PartnerAcceptRequestListView(APIView):
    permission_classes = [IsOrganizerUser]
    def get(self, request,id):
        organizer_id=request.id
        event=EventModel.objects.get(id=id)
        if event.has_accepted:
            return Response({"This event already confirmed"})
        partnerlist = OrganizerSendRequestToPartner.objects.filter(organizer_id=organizer_id,event_id=id,status='accepted')
        serializer = OrganizerSelectPartnerSerializer(partnerlist, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class OrganizerConfirmPartner(APIView):
    permission_classes = [IsOrganizerUser]

    def post(self, request):
        organizer = request.user  # Get the logged-in organizer
        partner_id = request.data.get('partner_id')
        event_id = request.data.get('event_id')

        
        try:
            partner = DispozenUser.objects.get(id=partner_id)
        except DispozenUser.DoesNotExist:
            return Response({"detail": "Partner not found."}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            event = EventModel.objects.get(id=event_id, organizer_id=organizer)
        except EventModel.DoesNotExist:
            return Response({"detail": "Event not found or you do not have permission to confirm this partner."}, status=status.HTTP_404_NOT_FOUND)
        if event.has_accepted:
            return Response({"detail": "Partner already confirmed for this event."},status=status.HTTP_400_BAD_REQUEST)


        event.partner_name = partner
        event.has_accepted = True
        event.save()


        # Only create if it doesn't exist
        if not PartnerSuccessfulEvent.objects.filter(partner_id=partner, event_id=event).exists():
            PartnerSuccessfulEvent.objects.create(
            partner_id=partner,
            event_id=event,
            created_at=event.created_at
            )
            return Response({"detail": "Partner successfully confirmed for the event."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"detail": "Partner already confirmed for this event."}, status=status.HTTP_400_BAD_REQUEST)


class ConfirmEventListView(APIView):
    permission_classes = [IsOrganizerUser]

    def get(self, request):
        organizer = request.user
        events = EventModel.objects.filter(organizer_id=organizer.id, conformation=True,has_accepted=True)
        
        serializer = ConfirmEventSerializer(events, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
        


    


class EventDeleteView(APIView):
    permission_classes = [IsOrganizerUser]

    def delete(self, request, id):
        organizer = request.user
        try:
            event = EventModel.objects.get(id=id, organizer_id=organizer.id)
            event.delete()
            return Response({"message": "Event deleted successfully."}, status=status.HTTP_200_OK)
        except EventModel.DoesNotExist:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)








class PaymentListView(APIView):
    permission_classes = [IsOrganizerUser|IsPartnerUser]
    def get(self, request):
        user = request.user
        payments = PaymentModel.objects.filter(user_id=user.id).order_by('-payment_date')

        
        serializer = PaymentModelSerializer(payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
class OrganizerPartnerUpdateProfileView(APIView):
    permission_classes = [IsOrganizerUser|IsPartnerUser]
    def put(self, request):
        user = request.user
        serializer = OrganizerPartnerProfileUpdateSerializer(user, data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile information updated successfully.", "user": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class OrganizerPartnerDealListView(APIView):
    permission_classes = [IsOrganizerUser]
    def get(self, request):
        organizer = request.user
        deals = OrganizerSendRequestToPartner.objects.filter(organizer_id=organizer.id,status='accepted')
        paginator = CustomPageNumberPagination()
        paginated_deals = paginator.paginate_queryset(deals, request)
        serializer = OrganizerSendRequestToPartnerSerializer(paginated_deals, many=True)
        return paginator.get_paginated_response(serializer.data)

class OrganizerPartnerDealView(APIView):
    permission_classes = [IsOrganizerUser]
    def get(self, request,id):
        
        try:
            deals = OrganizerSendRequestToPartner.objects.get(id=id)
        except OrganizerSendRequestToPartner.DoesNotExist:
            return Response({"detail": "Deal not found."}, status=status.HTTP_404_NOT_FOUND)
        
        partner_id=deals.partner_id
        event_id=deals.event_id
        
        
        partner = partner_id  
        event = event_id      

        if PartnerSuccessfulEvent.objects.filter(partner_id=partner, event_id=event).exists():
            return Response({"detail": "Partner and event already linked."}, status=status.HTTP_400_BAD_REQUEST)

        record = PartnerSuccessfulEvent.objects.create(partner_id=partner, event_id=event)

        serializer = PartnerSuccessfulEventSerializer(record)
        return Response({"message": "Partner and organizer deal done successfully.", "data": serializer.data}, status=status.HTTP_201_CREATED)

class SendEventEmailsView(APIView):
    permission_classes = [IsOrganizerUser]
    def get(self, request, event_id):
        
        event = get_object_or_404(EventModel, pk=event_id)

    
        subject = f"Reminder for Event: {event.event_name}" 
        message = f"Dear Guest, don't forget about our upcoming event: {event.event_name}. See you there!"

    
        success = send_event_email(event_id, subject, message)

        if success:
            return Response(
                {"message": f"Emails sent to all guests for event: {event.event_name}"},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"message": "No guests found for this event."},
                status=status.HTTP_404_NOT_FOUND
            )


# Partner Dashboard Website
class PartnerDashboardSuccessfullEventView(APIView):
    permission_classes = [IsPartnerUser]
    def get(self, request):
        partner = request.user
        events = PartnerSuccessfulEvent.objects.filter(partner_id=partner.id)
        
        serializer = PartnerSuccessfulEventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class PartnerRequestListView(APIView):
    permission_classes = [IsPartnerUser]
    def get(self, request):
        partner = request.user
        organizer_requests = OrganizerSendRequestToPartner.objects.filter(partner_id=partner.id, status='pending')
        
        serializer = OrganizerSendRequestToPartnerSerializer(organizer_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
class EventListShowtoPartnerView(APIView):
    permission_classes = [IsPartnerUser]
    def get(self, request,id):
        
        events = EventModel.objects.filter(organizer_id=id, has_accepted=True)
        
        serializer = OrganizerEventShowtoPartnerSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class EventRequestAcceptByPartnerView(APIView):
    permission_classes = [IsPartnerUser]
    
    def post(self, request):
        partner = request.user
        
        organizer_id = request.data.get('organizer_id')
        event_id = request.data.get('event_id')
        status_request = request.data.get('status')
        
        try:
            event = EventModel.objects.get(id=event_id)
        except EventModel.DoesNotExist:
            return Response({"detail": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            organizer = DispozenUser.objects.get(id=organizer_id)
        except DispozenUser.DoesNotExist:
            return Response({"detail": "Organizer not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already accepted
        if OrganizerSendRequestToPartner.objects.filter(
            event_id=event_id, 
            partner_id=partner.id, 
            organizer_id=organizer_id,
            status='accepted'
        ).exists():
            return Response(
                {"detail": "You have already accepted this request."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the pending request
        partnerAcceptRequest = OrganizerSendRequestToPartner.objects.filter(
            event_id=event.id, 
            partner_id=partner.id, 
            organizer_id=organizer.id
        ).order_by('-created_at').first()
        
        if not partnerAcceptRequest:
            return Response(
                {"detail": "No pending request found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update request status
        partnerAcceptRequest.status = status_request
        partnerAcceptRequest.save()
        
        # Create notification for ORGANIZER
        notification = Notification.objects.create(
            partner=partner,  # Who accepted
            organizer=organizer,  # Who will receive notification
            event=event,
            title='Partner Request Accepted',
            content=f'{partner.name} has accepted your event request.',
            notification_type='acceptance',
            is_read=False,
        )
        
        # Send real-time notification to ORGANIZER
        channel_layer = get_channel_layer()
        notification_message = {
            "id": notification.id,
            "content": notification.content,  # Only content needed
        }
        
        try:
            # ✅ FIX: Send to organizer's WebSocket group
            async_to_sync(channel_layer.group_send)(
                f"user_{organizer.id}",  # ✅ FIXED: Use organizer.id, not event.organizer_id
                {
                    "type": "send_notification",
                    "message": notification_message,
                }
            )
            print(f"✅ Notification sent to organizer {organizer.id} via WebSocket")
        except Exception as e:
            print(f"❌ Failed to send WebSocket notification: {str(e)}")

        return Response({
            "message": "Event request accepted successfully",
        }, status=status.HTTP_200_OK)
    

class PartnerRequestConfirmationView(APIView):
    permission_classes = [IsPartnerUser]
    def post(self, request, id):
        partner = request.user
        
        user_status=request.data.get('status')
        
        try:
            request = OrganizerSendRequestToPartner.objects.get(id=id)
        except OrganizerSendRequestToPartner.DoesNotExist:
            return Response({"detail": "Request not found."}, status=status.HTTP_404_NOT_FOUND)
        request.status = user_status
        print(request.status)
        request.save()
        return Response({"detail": "Request confirmed successfully."}, status=status.HTTP_200_OK)

class PartnerConfirmEventListView(APIView):
    permission_classes = [IsPartnerUser]
    def get(self, request):
        partner = request.user
        requests = OrganizerSendRequestToPartner.objects.filter(partner_id=partner.id, status='accepted')
        paginator = CustomPageNumberPagination()
        paginated_requests = paginator.paginate_queryset(requests, request)
        serializer = OrganizerSendRequestToPartnerSerializer(paginated_requests, many=True)
        return paginator.get_paginated_response(serializer.data)






# ManyChat Integration Views

class CheckUserView(APIView):
    def get(self,request,id):
        
        try:
            user=DispozenUser.objects.get(fb_id=id)
            print(id,user)
            if user.is_verified==False:
                return Response({False},status=400)
            return Response({
                "is_varified":user.is_verified,
                "fb_id":user.fb_id, 
                "id":user.id,
                "role":user.role
                }, status=200)
        except DispozenUser.DoesNotExist:
            return Response({"error":"User not found"},status=404)
        
        



class CreateEventView(APIView):
    """
    API View to create a new event
    """
    
    def post(self, request):
        serializer = CreateEventModelSerializer(data=request.data)
        
        if serializer.is_valid():
            event = serializer.save()
            
            event_id=event.id^1011
            print(event_id^1011)
            response_data = {
                "Event id":event_id,
                'message': 'Event created successfully'
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventInvitationView(APIView):
    def get(self, request, id):
        id=id^1011
        event=get_object_or_404(EventModel, id=id)
        serializer = CreateEventModelSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GuestVotingView(APIView):
    def post(self, request):
        serializer=GuestVotingSerializer(data=request.data)
        event_id=request.data.get("event_id")
        email=request.data.get("email")
        vote=request.data.get("vote")
        schedule=request.data.get("schedule")
        event_id=int(event_id)^1011
        event=get_object_or_404(EventModel, id=event_id)
        if int(schedule)==1:
            if int(vote)==int(1):
                event.schedule1_going+=1
            elif int(vote)==int(2):
                event.schedule1_not_going+=1
            else:
                event.schedule1_maybe+=1
        else:
            if int(vote)==1:
                event.schedule2_going+=1
            elif int(vote)==2:
                event.schedule2_not_going+=1
            else:
                event.schedule2_maybe+=1
        event.save()
        print(event_id, email, vote, schedule)
        # Save guest email (and optional vote/schedule) for this event
        if email:
            try:
                GuestEmail.objects.create( eventId=event,email=email)
            except Exception as e:
                print(f"Failed to save GuestEmail: {e}")
        return Response(True)
    
class DateTimeModificationView(APIView):
    def post(self, request):
        # Extract the data from the request
        data = request.data
        serializer = DateTimeModificationSerializer(data=data)

        
        day_time = data.get("date_time")
        
        iso_code=data.get("iso_code")
        
        if not day_time:
            return Response({"error": "'date_time' field is required."}, status=400)
        
        # Try to parse 'date_time' if it exists
        try:
            day_time = datetime.fromisoformat(day_time)  # Convert the ISO string to a datetime object

        except ValueError:
            return Response({"error": "Invalid 'date_time' format. Please use ISO 8601 format."}, status=400)

        # Make 'current_time' aware by adding UTC timezone (or use the same timezone as 'day_time')
        current_time = datetime.now(pytz.utc)  # Use UTC timezone here, or change to match 'day_time' timezone
        
        # Compare times (both now aware)
        if day_time <= current_time:
            return Response({"date_time": None, }, status=400)

        date = day_time.strftime('%d/%m/%Y')  # Format the date as day/month/year
        date_obj = datetime.strptime(date, '%d/%m/%Y')
        date = date_obj.strftime('%d-%b-%Y')
        time_str = day_time.strftime('%H:%M')  # Format the time as hours:minutes

        
        result=convert_utc_to_local(day_time.time(),iso_code)
    
        time_str = result.strftime('%I:%M %p')
        return Response({"date_time": f"{date} {time_str}"}, status=200)
        
class MapView(APIView):
    def get(self, request):
        location = request.GET.get('location', '')  
        category = request.GET.get('catagory', '')  
        sub_category = request.GET.get('sub-catagory', '')

        # Check if required parameters are provided
        if not location or not category or not sub_category:
            return Response({'error': 'Missing required parameters (location, category, sub-category)'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Geocode the location (returns lat, lon)
        try:
            lan, lon = geocode_location(location)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Format the location as "lat,lon"
        location = f"{lan},{lon}"

        radius = request.query_params.get('radius', 1500)  # Default to 1500 meters
        type_ = sub_category  # This will be passed as 'type'
        keyword = category  # This will be passed as 'keyword'
        api_key = config('maps_key')
        organizerlocation=DispozenUser.objects.filter(role='partner')
        l=[]

        for i in organizerlocation:
            g1,g2=geocode_location(i.location)
            
            l.append([g1,g2])
        print(l)
        # Construct the Google Places API URL dynamically
        url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&type={type_}&keyword={keyword}&key={api_key}'
        
        try:
            # Make the API request to Google Places
            response = urllib.request.urlopen(url)
            data = json.loads(response.read().decode('utf-8'))

            # Check if the status is OK and results exist
            if data.get('status') == 'OK' and 'results' in data:
                places = []
                for place in data['results']:
                    # if [place['geometry']['location']['lat'],place['geometry']['location']['lng']] in l:
                        places.append({
                            'name': place.get('name'),
                            'address': place.get('vicinity'),
                            'latitude': place['geometry']['location']['lat'],
                            'longitude': place['geometry']['location']['lng'],
                        })

                # Return the response with list of places
                return Response({'places': places}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'No results found or API request failed'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Catch any request-related errors
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
# def map_view(request):
#     # context = {
#     #     'location': request.GET.get('location', 'Khulna'),
#     #     'type': request.GET.get('type', 'private'),
#     #     'keyword': request.GET.get('keyword', 'Hospital'),
#     # }
#     return render(request, 'map_view.html')

from rest_framework.decorators import api_view

from django.views.decorators.csrf import csrf_exempt
from decouple import config
import json
from .models import SelectedPlace

# Your existing MapView stays the same

def map_view(request,organizer_id):
    
    
    # Pass the API key securely to the template
    context = {
        'maps_api_key': config('maps_key'),
        'id':organizer_id
    
    }
    print(context)
    return render(request, 'map_view.html', context)


from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from decouple import config
from .models import SelectedPlace, DispozenUser
import json


def map_view(request, organizer_id):
    """
    Render the map view template with API key and organizer_id
    """
    context = {
        'maps_api_key': config('maps_key'),
        'organizer_id': organizer_id
    }
    print(context)
    return render(request, 'map_view.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class SelectPlaceView(APIView):
    """
    API View to save selected place to database with organizer as ForeignKey
    """
    
    def post(self, request):
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['name', 'address', 'latitude', 'longitude', 'organizer_id']
            for field in required_fields:
                if field not in data:
                    return Response(
                        {'error': f'Missing required field: {field}'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Get the DispozenUser instance using the organizer_id
            try:
                organizer = DispozenUser.objects.get(fb_id=data.get('organizer_id'))
                
            except DispozenUser.DoesNotExist:
                return Response(
                    {'error': 'Organizer not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create the selected place
            selected_place = SelectedPlace.objects.create(
                name=data.get('name'),
                address=data.get('address'),
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                category=data.get('category'),
                sub_category=data.get('sub_category'),
                location=data.get('location'),
                organizer=organizer  # Assign the DispozenUser instance
            )
            print(selected_place)
            return Response({
                'success': True,
                'message': 'Place selected successfully',
                'place_id': selected_place.id,
                'organizer_id': selected_place.organizer.fb_id  # ✅ Changed from organizer_id.id to organizer.fb_id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )