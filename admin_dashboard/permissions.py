from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users to access admin endpoints.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow read-only access to all authenticated users, but write access only to admins.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')