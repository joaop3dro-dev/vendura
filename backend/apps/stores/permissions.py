from rest_framework.permissions import BasePermission


class IsSeller(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "store")
            and request.user.store.is_active
        )


class IsSellerOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.store == request.user.store
