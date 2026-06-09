from rest_framework import serializers
from .models import Supplier, Batch


class SupplierSerializer(serializers.ModelSerializer):
    # Frontend treats these as optional; the model column is NOT NULL but accepts ''.
    phone = serializers.CharField(required=False, allow_blank=True, default='')
    contact_person = serializers.CharField(required=False, allow_blank=True, default='')
    email = serializers.CharField(required=False, allow_blank=True, default='')
    address = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = Supplier
        fields = '__all__'


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = '__all__'
