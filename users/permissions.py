# users/permissions.py
from rest_framework import permissions


class IsCashier(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.userrole_set.filter(role__name='cashier').exists() or \
               request.user.userrole_set.filter(role__name='administrator').exists()


class IsAccountant(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.userrole_set.filter(role__name='accountant').exists() or \
               request.user.userrole_set.filter(role__name='administrator').exists()


class IsStoreKeeper(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.userrole_set.filter(role__name='store_keeper').exists() or \
               request.user.userrole_set.filter(role__name='administrator').exists()


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.userrole_set.filter(role__name='administrator').exists()