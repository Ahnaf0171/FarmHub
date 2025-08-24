from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "admin"

class IsAgent(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "agent"

class IsFarmer(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "farmer"

class IsAdminOrAgent(BasePermission):
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        return bool(getattr(u, "is_authenticated", False) and getattr(u, "role", None) in {"admin", "agent"})

class IsFarmerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        return bool(getattr(u, "is_authenticated", False) and getattr(u, "role", None) in {"farmer", "admin"})

class AuthenticatedOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(getattr(request.user, "is_authenticated", False))

class PostAdminOrAgentElseAuth(BasePermission):
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        if not getattr(u, "is_authenticated", False):
            return False
        if request.method in SAFE_METHODS:
            return True
        return getattr(u, "role", None) in {"admin", "agent"}

class PostFarmerOrAdminElseAuth(BasePermission):
    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        if not getattr(u, "is_authenticated", False):
            return False
        if request.method in SAFE_METHODS:
            return True
        return getattr(u, "role", None) in {"farmer", "admin"}

