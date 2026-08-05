from rest_framework.permissions import BasePermission

from .models import Customer


class CanDeactivateCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("customers.deactivate_customer")

    def has_object_permission(self, request, view, obj):
        return obj.status == Customer.Status.ACTIVE
