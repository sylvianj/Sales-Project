# returns/serializers.py
from rest_framework import serializers
from .models import Return

class ReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Return
        fields = '__all__'