from django.shortcuts import render

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Vehicle
from .serializers import VehicleSerializer, VehicleCreateSerializer
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import redirect
from django.contrib import messages
from rest_framework import status



# class RegisterVehicleView(APIView):
#     """Register a new vehicle for the driver"""
#     permission_classes = [permissions.IsAuthenticated]
    
#     def post(self, request):
#         if not request.user.is_driver:
#             return Response({'error': 'Only drivers can register vehicles'}, 
#                           status=status.HTTP_403_FORBIDDEN)
        
#         # Check if driver already has a vehicle
#         if hasattr(request.user, 'vehicle'):
#             return Response({'error': 'You already have a registered vehicle'}, 
#                           status=status.HTTP_400_BAD_REQUEST)
        
#         serializer = VehicleCreateSerializer(data=request.data)
#         if serializer.is_valid():
#             vehicle = serializer.save(driver=request.user)
#             return Response(VehicleSerializer(vehicle).data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.authentication import SessionAuthentication


# @method_decorator(csrf_exempt, name='dispatch')
# class RegisterVehicleView(APIView):
#     """Register a new vehicle for the driver"""
#     authentication_classes = [SessionAuthentication]  # Override to use session auth

#     permission_classes = [permissions.IsAuthenticated]
    
#     def post(self, request):
#         # Debug info
#         print(f"User: {request.user}")
#         print(f"Is authenticated: {request.user.is_authenticated}")
        
#         # Check authentication
#         if not request.user.is_authenticated:
#             return Response({'error': 'Please log in first'}, status=status.HTTP_401_UNAUTHORIZED)
        
#         # Check if user is driver
#         if request.user.role != 'driver':
#             return Response({'error': 'Only drivers can register vehicles'}, 
#                           status=status.HTTP_403_FORBIDDEN)
        
#         # Check if driver already has a vehicle
#         if hasattr(request.user, 'vehicle'):
#             return Response({'error': 'You already have a registered vehicle'}, 
#                           status=status.HTTP_400_BAD_REQUEST)
        
#         # Process the form data
#         serializer = VehicleCreateSerializer(data=request.data)
#         if serializer.is_valid():
#             vehicle = serializer.save(driver=request.user)
#             return Response(VehicleSerializer(vehicle).data, status=status.HTTP_201_CREATED)
        
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class RegisterVehicleView(APIView):
    """Register a new vehicle for the driver"""
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Debug info
        print(f"User: {request.user}")
        print(f"Is authenticated: {request.user.is_authenticated}")
        
        # Check authentication
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in first')
            return redirect('/login/')
        
        # Check if user is driver
        if request.user.role != 'driver':
            messages.error(request, 'Only drivers can register vehicles')
            return redirect('/driver/dashboard/')
        
        # Check if driver already has a vehicle
        if hasattr(request.user, 'vehicle'):
            messages.error(request, 'You already have a registered vehicle')
            return redirect('/driver/dashboard/')
        
        # Process the form data
        serializer = VehicleCreateSerializer(data=request.data)
        if serializer.is_valid():
            vehicle = serializer.save(driver=request.user)
            messages.success(request, f'Vehicle {vehicle.make} {vehicle.model} registered successfully!')
            return redirect('/driver/dashboard/')
        
        # If validation fails, show errors and redirect back
        for field, errors in serializer.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')
        return redirect('/driver/dashboard/')
    
class UpdateVehicleView(APIView):
    """Update existing vehicle"""
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request):
        if not request.user.is_driver:
            return Response({'error': 'Only drivers can update vehicles'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if not hasattr(request.user, 'vehicle'):
            return Response({'error': 'No vehicle found. Please register first.'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        vehicle = request.user.vehicle
        serializer = VehicleCreateSerializer(vehicle, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(VehicleSerializer(vehicle).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class GetVehicleView(APIView):
#     """Get driver's vehicle information"""
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get(self, request):
#         if request.user.is_driver and hasattr(request.user, 'vehicle'):
#             return Response(VehicleSerializer(request.user.vehicle).data)
#         return Response({'vehicle': None}, status=status.HTTP_200_OK)


class GetVehicleView(APIView):
    """Get driver's vehicle information"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'vehicle': None}, status=status.HTTP_200_OK)
        
        if request.user.is_driver and hasattr(request.user, 'vehicle'):
            return Response(VehicleSerializer(request.user.vehicle).data)
        return Response({'vehicle': None}, status=status.HTTP_200_OK)