# users/serializers.py
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
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class UserRoleSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role', 'user_name', 'role_name', 'assigned_at']