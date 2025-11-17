
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import DispozenUserRegistrationView,OTPVerificationView,SendOTPView,DispozenUserLoginView,DispozenUserChangePasswordView,DispozenUserForgotPasswordResetView,DispozenAdminAccountSettingProfileView,DispozenUserDisableAccountView,DispozenAdminUpdateProfileView
from .views import SuperAdminCreateAccountView,admininfo,DispozenAdminListView, DispozenOrganizerListView,DispozenPartnerListView,Delete_User,DispozenUsersOverView,RequestEventView
from .views import ConfirmEventListView,InitialConfirmViewList,PartnerListView,EventDeleteView,OrganizerPartnerDealListView,OrganizerPartnerDealView,AllEventList,PartnerAcceptRequestListView,PartnerSuccessfulEventView,PaymentListView,  EventSchedulesConfirm,OrganizerPartnerUpdateProfileView,OrganizerConfirmPartner,SendEventEmailsView
from .views import PartnerDashboardSuccessfullEventView,PartnerRequestListView,PartnerRequestConfirmationView,PartnerConfirmEventListView,EventListShowtoPartnerView,EventRequestAcceptByPartnerView
from .views import CheckUserView,CreateEventView,DateTimeModificationView,EventInvitationView,GuestVotingView,MapView,SelectPlaceView,OrganizerFinalLocation
from .views import map_view,payment_page,payment_success_page
from .views import (
    CreatePaymentIntentView, 
    PaymentSuccessView, 
    StripeWebhookView,
    PaymentHistoryView
)

urlpatterns = [
    # Token Refresh Endpoint
    path('refresh-token/', TokenRefreshView.as_view(), name='token-refresh'),
    # Authentication Endpoints
    path('register/', DispozenUserRegistrationView.as_view(), name='register'),
    path('login/', DispozenUserLoginView.as_view(), name='login'),
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('otp-verify/', OTPVerificationView.as_view(), name='otp-verify'),
    path('forgot-password-reset/', DispozenUserForgotPasswordResetView.as_view(), name='forgot-password-reset'),
    path('change-password/', DispozenUserChangePasswordView.as_view(), name='change-password'),
    path('disable-account/<int:id>/', DispozenUserDisableAccountView.as_view(), name='disable-account'),
    
    # path('enable-account/', DispozenUserEnableAccountView.as_view(), name='enable-account'),
    
    path('account/', DispozenAdminAccountSettingProfileView.as_view(), name='update-profile-picture'),
    # Admin Management Endpoints
    #Admin Dashboard Endpoints
    path('super-admin-create-account/', SuperAdminCreateAccountView.as_view(), name='super-admin-create-account'),
    path('admin-info/', admininfo.as_view(), name='admin-info'),
    path('admin-list/', DispozenAdminListView.as_view(), name='admin-list'),
    path('admin-delete/<int:id>/', Delete_User.as_view(), name='admin-delete'),
    path('organizer-list/', DispozenOrganizerListView.as_view(), name='organizer-list'),
    path('partner-list/', DispozenPartnerListView.as_view(), name='partner-list'),
    path('users-overview/', DispozenUsersOverView.as_view(), name='users-overview'),
    path('update-admin-profile/', DispozenAdminUpdateProfileView.as_view(), name='update-admin-profile'),
    # path('delete-organizer-partner/<int:id>/', AdminDeleteOrganizerPartnerView.as_view(), name='delete-organizer-partner'),
    # path('organizer-events/<int:id>/', AdminOrganizerEventView.as_view(), name='organizer-events'),

    # Organizer management Endpoints
    path('all-events/', AllEventList.as_view(), name='all-events'),
    path('event-schedules-confirm/<int:id>/', EventSchedulesConfirm.as_view(), name='event-schedules-confirm'),
    path('initial-confirmation-events/', InitialConfirmViewList.as_view(), name='all-pending-events'),
    path('all-partner/', PartnerListView.as_view(), name='all-partner'),
    path('partner-event-list/<int:id>/', PartnerSuccessfulEventView.as_view(), name='partner-event-list'),
    path('request-event/', RequestEventView.as_view(), name='request-event'),
    path('accepted-partner-list/<int:id>/', PartnerAcceptRequestListView.as_view(), name='organizer-select-partner'),
    path('organizer-confirm-partner/',OrganizerConfirmPartner.as_view(),name="Organizer-confirm-partner"),
    path('confirm-event-list/', ConfirmEventListView.as_view(), name='all-confirm-events'),
    
    
    path('delete-event/<int:id>/', EventDeleteView.as_view(), name='delete-event'),
    
    
    
    
    path('payment-list/', PaymentListView.as_view(), name='payment-list'),
    path('organizer-partner-update-profile/', OrganizerPartnerUpdateProfileView.as_view(), name='organizer-partner-update-profile'),
    path('send_emails/<int:event_id>/', SendEventEmailsView.as_view(), name='send_event_emails'),
    # path('organizer-send-request/', OrganizerSendRequestToPartnerView.as_view(), name='organizer-send-request'),
    path('organizer-partner-deal-list/', OrganizerPartnerDealListView.as_view(), name='organizer-partner-deal-list'),
    path('organizer-partner-deal/<int:id>/', OrganizerPartnerDealView.as_view(), name='organizer-partner-deal'),
    # Partner Management Endpoints
    path('partner-successful-events/', PartnerDashboardSuccessfullEventView.as_view(), name='partner-successful-events'),
    path('partner-request-list/', PartnerRequestListView.as_view(), name='partner-request-list'),
    path('event-list-show-to-partner/<int:id>/', EventListShowtoPartnerView.as_view(), name='event-list-show-to-partner'),
    path('event-request-accept-by-partner/', EventRequestAcceptByPartnerView.as_view(), name='event-request-accept-by-partner'),
    path('partner-request-confirmation/<int:id>/', PartnerRequestConfirmationView.as_view(), name='partner-request-confirmation'),
    path('partner-confirm-event-list/', PartnerConfirmEventListView.as_view(), name='partner-confirm-event-list'),
    # ManyChat Endpoints
    path('check-user/<str:id>/', CheckUserView.as_view(), name='check-user'),
    path('create-event/', CreateEventView.as_view(), name='create_event'),
    path('event-invitation/<int:id>/', EventInvitationView.as_view(), name='event-invitation'),
    path('voting/',GuestVotingView.as_view(),name="Guest_voting"),
    path("datetime-modify/",DateTimeModificationView.as_view(),name="datetime-modify"),
    path("maps/",MapView.as_view()),
    path('maps_view/<str:organizer_id>/',map_view,name='map_view'),
    path('select-place/', SelectPlaceView.as_view(), name='select_place'),
    path('organizer-location/<str:fb_id>/',OrganizerFinalLocation.as_view(),name='Organizer_final_location'),

    path('create-payment-intent/', CreatePaymentIntentView.as_view(), name='create_payment_intent'),
    path('payment-success/', PaymentSuccessView.as_view(), name='payment_success'),
    path('stripe-webhook/', StripeWebhookView.as_view(), name='stripe_webhook'),
    path('payment-history/<str:fb_id>/', PaymentHistoryView.as_view(), name='payment_history'),
    path('payment/', payment_page, name='payment_page'),
    # path('payment-success/', payment_success_page, name='payment_success_page'),
    path('payment-success.html', payment_success_page, name='payment_success_page'),  
]
