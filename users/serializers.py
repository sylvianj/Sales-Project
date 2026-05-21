# users/serializers.py - COMPLETE FILE
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Role, UserRole


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'roles']
    
    def get_roles(self, obj):
        return [role.name for role in obj.userrole_set.all().select_related('role')]


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, help_text="Username")
    password = serializers.CharField(required=True, write_only=True, help_text="Password")