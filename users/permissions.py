# users/permissions.py - COMPLETE FILE
from rest_framework import permissions


class IsCashier(permissions.BasePermission):
    """Allow access only to cashier or admin"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.userrole_set.filter(role__name='cashier').exists() or \
               request.user.userrole_set.filter(role__name='administrator').exists()


class IsAccountant(permissions.BasePermission):
    """Allow access only to accountant or admin"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.userrole_set.filter(role__name='accountant').exists() or \
               request.user.userrole_set.filter(role__name='administrator').exists()


class IsStoreKeeper(permissions.BasePermission):
    """Allow access only to store keeper or admin"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.userrole_set.filter(role__name='store_keeper').exists() or \
               request.user.userrole_set.filter(role__name='administrator').exists()


class IsAdmin(permissions.BasePermission):
    """Allow access only to administrator"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.userrole_set.filter(role__name='administrator').exists()