from rest_framework import permissions
from .models import DispozenUser

class IsSuperAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        print(getattr(request.user, 'superuserstatus', False))
        return bool(request.user and request.user.is_authenticated and (
            getattr(request.user, 'is_superuser', False) or
            getattr(request.user, 'role', '') == 'superadmin'
        ))
class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'
class IsPartnerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'partner' 
class IsOrganizerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'organizer' 