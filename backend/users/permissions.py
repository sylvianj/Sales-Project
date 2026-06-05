# users/permissions.py
from rest_framework import permissions


class HasRole(permissions.BasePermission):
    required_role = None

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not self.required_role:
            return False
        return request.user.userrole_set.filter(role__name__in=[self.required_role, 'administrator']).exists()


class IsCashier(HasRole):
    required_role = 'cashier'


class IsAccountant(HasRole):
    required_role = 'accountant'


class IsStoreKeeper(HasRole):
    required_role = 'store_keeper'


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.userrole_set.filter(role__name='administrator').exists()