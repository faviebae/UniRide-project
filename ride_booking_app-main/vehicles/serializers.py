from rest_framework import serializers
from .models import Vehicle

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'make', 'model', 'year', 'color', 'license_plate', 'photo', 'is_approved', 'created_at']
        read_only_fields = ['id', 'is_approved', 'created_at']

class VehicleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['make', 'model', 'year', 'color', 'license_plate', 'photo']