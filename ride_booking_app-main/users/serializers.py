from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, DriverProfile, StudentProfile
from rest_framework_simplejwt.tokens import RefreshToken

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 
                  'phone_number', 'role', 'avatar', 'wallet_balance', 
                  'is_verified', 'created_at']
        read_only_fields = ['wallet_balance', 'is_verified', 'created_at']

class DriverProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = DriverProfile
        fields = '__all__'
        read_only_fields = ['total_trips', 'total_earnings', 'rating']

class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = StudentProfile
        fields = '__all__'
        read_only_fields = ['total_trips', 'total_spent']

# class RegisterSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True, min_length=8)
#     confirm_password = serializers.CharField(write_only=True)
    
#     class Meta:
#         model = User
#         fields = ['email', 'first_name', 'last_name', 'phone_number', 
#                   'password', 'confirm_password', 'role']
    
#     def validate(self, data):
#         if data['password'] != data['confirm_password']:
#             raise serializers.ValidationError("Passwords don't match")
#         return data
    
#     def create(self, validated_data):
#         validated_data.pop('confirm_password')
#         user = User.objects.create_user(**validated_data)
        
#         # Create role-specific profile
#         if user.role == 'driver':
#             DriverProfile.objects.create(user=user)
#         elif user.role == 'student':
#             StudentProfile.objects.create(user=user)
        
#         return user


# class RegisterSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True, min_length=8)
#     confirm_password = serializers.CharField(write_only=True)
    
#     class Meta:
#         model = User
#         fields = ['email', 'first_name', 'last_name', 'phone_number', 
#                   'password', 'confirm_password', 'role']
    
#     def validate(self, data):
#         if data['password'] != data['confirm_password']:
#             raise serializers.ValidationError("Passwords don't match")
#         return data
    
#     def create(self, validated_data):
#         validated_data.pop('confirm_password')
#         user = User.objects.create_user(**validated_data)
        
#         if user.role == 'driver':
#             DriverProfile.objects.create(
#                 user=user,
#                 license_number='PENDING',  # Placeholder
#                 license_expiry=None,  # Will be updated later
#                 is_available=False
#             )
#         elif user.role == 'student':
#             StudentProfile.objects.create(user=user)
        
#         return user

from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, DriverProfile, StudentProfile
from rest_framework_simplejwt.tokens import RefreshToken

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    # Driver license fields
    license_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    license_expiry = serializers.DateField(required=False, allow_null=True)
    license_photo = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 
                  'password', 'confirm_password', 'role',
                  'license_number', 'license_expiry', 'license_photo']
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate driver license fields if role is driver
        if data.get('role') == 'driver':
            if not data.get('license_number'):
                raise serializers.ValidationError({"license_number": "License number is required for drivers"})
            if not data.get('license_expiry'):
                raise serializers.ValidationError({"license_expiry": "License expiry date is required for drivers"})
        
        return data
    
    def create(self, validated_data):
        # Extract driver-specific fields
        license_number = validated_data.pop('license_number', None)
        license_expiry = validated_data.pop('license_expiry', None)
        license_photo = validated_data.pop('license_photo', None)
        
        # Remove confirm_password
        validated_data.pop('confirm_password')
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Create role-specific profile
        if user.role == 'driver':
            DriverProfile.objects.create(
                user=user,
                license_number=license_number or 'PENDING',
                license_expiry=license_expiry,
                license_photo=license_photo,
                is_available=False
            )
        elif user.role == 'student':
            StudentProfile.objects.create(user=user)
        
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        if not user.is_active:
            raise serializers.ValidationError("Account is deactivated")
        
        refresh = RefreshToken.for_user(user)
        return {
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }