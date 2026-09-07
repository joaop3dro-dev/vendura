from rest_framework.permissions import BasePermission

from .models import Order


class CanApproveOrder(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("orders.approve_order")

    def has_object_permission(self, request, view, obj):
        return obj.status == Order.Status.PENDING


class CanCancelOrder(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("orders.cancel_order")

    def has_object_permission(self, request, view, obj):
        return obj.status == Order.Status.PENDING
