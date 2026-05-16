from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from users.models import User
from bookings.models import Trip
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal
from django.db import models



# def index(request):
#     """Landing page"""
#     if request.user.is_authenticated:
#         if request.user.role == 'student':
#             return redirect('student_dashboard')
#         elif request.user.role == 'driver':
#             return redirect('driver_dashboard')
#         elif request.user.role == 'admin':
#             return redirect('admin_dashboard')
#     return render(request, 'index.html')

def index(request):
    """Homepage view"""
    # if request.user.is_authenticated:
    if request.user.is_authenticated and not request.user.is_superuser:
        if request.user.role == 'student':
            return redirect('bookings:student_dashboard')
        elif request.user.role == 'driver':
            return redirect('bookings:driver_dashboard')
        elif request.user.role == 'admin':
            return redirect('bookings:admin_dashboard')
    return render(request, 'index.html', {
        'title': 'Welcome to RideBook',
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    })

# bookings/views.py - Add these new functions

# def registration_page(request):
#     """Display registration page"""
#     if request.user.is_authenticated:
#         if request.user.role == 'student':
#             return redirect('student_dashboard')
#         elif request.user.role == 'driver':
#             return redirect('driver_dashboard')
#         elif request.user.role == 'admin' or request.user.is_superuser:
#             return redirect('admin_dashboard')
#     return render(request, 'register.html', {
#         'title': 'Register - RideBook'
#     })

# def login_page(request):
#     """Display login page"""
#     if request.user.is_authenticated:
#         if request.user.role == 'student':
#             return redirect('student_dashboard')
#         elif request.user.role == 'driver':
#             return redirect('driver_dashboard')
#         elif request.user.role == 'admin' or request.user.is_superuser:
#             return redirect('admin_dashboard')
#     return render(request, 'login.html', {
#         'title': 'Login - RideBook'
#     })

# @login_required
# def student_dashboard(request):
#     """Student dashboard view"""
#     if request.user.role != 'student':
#         return redirect('index')
    
#     # Get active trip
#     active_trip = Trip.objects.filter(
#         student=request.user,
#         status__in=['searching', 'accepted', 'arrived', 'ongoing']
#     ).first()
    
#     # Get statistics
#     completed_trips = Trip.objects.filter(
#         student=request.user,
#         status='completed'
#     )
#     total_trips = completed_trips.count()
#     total_spent = completed_trips.aggregate(models.Sum('total_fare'))['total_fare__sum'] or 0
    
#     context = {
#         'active_trip': active_trip,
#         'total_trips': total_trips,
#         'total_spent': total_spent,
#         'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
#     }
#     return render(request, 'student/dashboard.html', context)

# @login_required
# def driver_dashboard(request):
#     """Driver dashboard view"""
#     if request.user.role != 'driver':
#         return redirect('index')
    
#     context = {
#         'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
#     }
#     return render(request, 'driver/dashboard.html', context)

# @login_required
# def admin_dashboard(request):
#     """Admin dashboard view"""
#     if request.user.role != 'admin':
#         return redirect('index')
    
#     # Get statistics
#     total_users = User.objects.count()
#     total_drivers = User.objects.filter(role='driver').count()
#     total_students = User.objects.filter(role='student').count()
#     total_trips = Trip.objects.count()
#     completed_trips = Trip.objects.filter(status='completed').count()
    
#     # Calculate revenue
#     total_revenue = Trip.objects.filter(
#         status='completed'
#     ).aggregate(models.Sum('total_fare'))['total_fare__sum'] or 0
    
#     context = {
#         'total_users': total_users,
#         'total_drivers': total_drivers,
#         'total_students': total_students,
#         'total_trips': total_trips,
#         'completed_trips': completed_trips,
#         'total_revenue': total_revenue,
#         'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
#     }
#     return render(request, 'admin/dashboard.html', context)



@login_required
def student_dashboard(request):
    """Student dashboard view"""
    if request.user.role != 'student':
        messages.error(request, 'Access denied. Student only area.')
        return redirect('bookings:index')
    
    # Get active trip if any
    active_trip = Trip.objects.filter(
        student=request.user,
        status__in=['requesting', 'searching', 'accepted', 'arrived', 'ongoing']
    ).first()
    
    # Get trip history
    trip_history = Trip.objects.filter(
        student=request.user,
        status__in=['completed', 'cancelled_by_student', 'cancelled_by_driver']
    ).order_by('-requested_at')[:10]
    
    context = {
        'title': 'Student Dashboard',
        'user': request.user,
        'active_trip': active_trip,
        'trip_history': trip_history,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    }
    return render(request, 'student/dashboard.html', context)

@login_required
def driver_dashboard(request):
    """Driver dashboard view"""
    if request.user.role != 'driver':
        messages.error(request, 'Access denied. Driver only area.')
        return redirect('bookings:index')
    
    # Get active trip if any
    active_trip = Trip.objects.filter(
        driver=request.user,
        status__in=['accepted', 'arrived', 'ongoing']
    ).first()
    
    # Get available ride requests
    ride_requests = Trip.objects.filter(
        status='searching'
    ).order_by('-requested_at')[:10]
    
    # Get trip history
    trip_history = Trip.objects.filter(
        driver=request.user,
        status__in=['completed', 'cancelled_by_driver']
    ).order_by('-completed_at')[:10]
    
    context = {
        'title': 'Driver Dashboard',
        'user': request.user,
        'active_trip': active_trip,
        'ride_requests': ride_requests,
        'trip_history': trip_history,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    }
    return render(request, 'driver/dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Admin dashboard view"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied. Admin only area.')
        return redirect('bookings:index')
    
    # Get statistics
    total_users = User.objects.count()
    total_students = User.objects.filter(role='student').count()
    total_drivers = User.objects.filter(role='driver').count()
    total_trips = Trip.objects.count()
    completed_trips = Trip.objects.filter(status='completed').count()
    active_trips = Trip.objects.filter(status__in=['searching', 'accepted', 'arrived', 'ongoing']).count()
    
    # Calculate revenue
    total_revenue = Trip.objects.filter(
        status='completed'
    ).aggregate(models.Sum('total_fare'))['total_fare__sum'] or 0
    
    # Recent trips
    recent_trips = Trip.objects.all().order_by('-requested_at')[:20]
    
    context = {
        'title': 'Admin Dashboard',
        'user': request.user,
        'total_users': total_users,
        'total_students': total_students,
        'total_drivers': total_drivers,
        'total_trips': total_trips,
        'completed_trips': completed_trips,
        'active_trips': active_trips,
        'total_revenue': total_revenue,
        'recent_trips': recent_trips,
    }
    return render(request, 'admin/dashboard.html', context)

# API Views
@login_required
def trip_list(request):
    """API endpoint to list trips"""
    if request.user.role == 'student':
        trips = Trip.objects.filter(student=request.user)
    elif request.user.role == 'driver':
        trips = Trip.objects.filter(driver=request.user)
    else:
        trips = Trip.objects.all()
    
    trips_data = []
    for trip in trips:
        trips_data.append({
            'id': trip.id,
            'pickup_address': trip.pickup_address,
            'dropoff_address': trip.dropoff_address,
            'status': trip.status,
            'total_fare': str(trip.total_fare),
            'requested_at': trip.requested_at.isoformat(),
            'driver_name': trip.driver.get_full_name() if trip.driver else None,
        })
    
    return JsonResponse({'trips': trips_data}, status=200)

@login_required
def trip_detail(request, trip_id):
    """API endpoint to get trip details"""
    trip = get_object_or_404(Trip, id=trip_id)
    
    # Check permission
    if request.user.role not in ['admin'] and request.user not in [trip.student, trip.driver]:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    trip_data = {
        'id': trip.id,
        'pickup_address': trip.pickup_address,
        'pickup_latitude': str(trip.pickup_latitude),
        'pickup_longitude': str(trip.pickup_longitude),
        'dropoff_address': trip.dropoff_address,
        'dropoff_latitude': str(trip.dropoff_latitude),
        'dropoff_longitude': str(trip.dropoff_longitude),
        'status': trip.status,
        'status_display': trip.get_status_display(),
        'distance_km': str(trip.distance_km),
        'duration_minutes': trip.duration_minutes,
        'total_fare': str(trip.total_fare),
        'requested_at': trip.requested_at.isoformat(),
        'accepted_at': trip.accepted_at.isoformat() if trip.accepted_at else None,
        'started_at': trip.started_at.isoformat() if trip.started_at else None,
        'completed_at': trip.completed_at.isoformat() if trip.completed_at else None,
    }
    
    if trip.driver:
        trip_data['driver'] = {
            'id': trip.driver.id,
            'name': trip.driver.get_full_name(),
            'phone': str(trip.driver.phone_number),
            'rating': 4.5,  # You'll calculate this from ratings
        }
    
    if trip.student:
        trip_data['student'] = {
            'id': trip.student.id,
            'name': trip.student.get_full_name(),
            'phone': str(trip.student.phone_number),
        }
    
    return JsonResponse(trip_data, status=200)

@login_required
@csrf_exempt
def cancel_trip(request, trip_id):
    """API endpoint to cancel a trip"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    trip = get_object_or_404(Trip, id=trip_id)
    
    # Check permission
    if request.user.role not in ['admin'] and request.user not in [trip.student, trip.driver]:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Check if trip can be cancelled
    if trip.status not in ['requesting', 'searching', 'accepted']:
        return JsonResponse({'error': 'Trip cannot be cancelled at this stage'}, status=400)
    
    data = json.loads(request.body)
    reason = data.get('reason', 'No reason provided')
    
    if request.user == trip.student:
        trip.cancel('student', reason)
        message = 'Trip cancelled successfully'
    elif request.user == trip.driver:
        trip.cancel('driver', reason)
        message = 'Trip cancelled successfully'
    else:
        trip.cancel('admin', reason)
        message = 'Trip cancelled by admin'
    
    return JsonResponse({'message': message, 'trip_id': trip.id}, status=200)

@login_required
@csrf_exempt
def book_ride(request):
    """API endpoint to book a new ride"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if request.user.role != 'student':
        return JsonResponse({'error': 'Only students can book rides'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Create trip
        trip = Trip.objects.create(
            student=request.user,
            pickup_address=data['pickup_address'],
            pickup_latitude=data['pickup_latitude'],
            pickup_longitude=data['pickup_longitude'],
            dropoff_address=data['dropoff_address'],
            dropoff_latitude=data['dropoff_latitude'],
            dropoff_longitude=data['dropoff_longitude'],
            distance_km=data.get('distance_km', 0),
            duration_minutes=data.get('duration_minutes', 0),
            status='searching'
        )
        
        # Calculate fare
        trip.calculate_fare()
        trip.save()
        
        return JsonResponse({
            'message': 'Ride booked successfully',
            'trip_id': trip.id,
            'trip': {
                'id': trip.id,
                'total_fare': str(trip.total_fare),
                'status': trip.status,
            }
        }, status=201)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def nearby_drivers(request):
    """API endpoint to get nearby drivers"""
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    radius = request.GET.get('radius', 5)
    
    if not lat or not lng:
        return JsonResponse({'drivers': [], 'error': 'Latitude and longitude required'}, status=400)
    
    # Find available drivers (simplified for now)
    drivers = User.objects.filter(
        role='driver',
        is_available=True,
        current_latitude__isnull=False
    )[:10]  # Limit to 10 for now
    
    drivers_data = []
    for driver in drivers:
        drivers_data.append({
            'id': driver.id,
            'name': driver.get_full_name(),
            'rating': 4.5,
            'vehicle': {
                'make': 'Toyota',
                'model': 'Camry',
                'color': 'White',
                'license_plate': 'ABC-123'
            } if hasattr(driver, 'vehicle') else None,
            'distance_km': 1.5,  # You'll calculate this
        })
    
    return JsonResponse({'drivers': drivers_data}, status=200)