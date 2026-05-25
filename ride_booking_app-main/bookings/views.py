from django.utils import timezone

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
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta, datetime

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
    
    if request.user.role != 'student':
        return JsonResponse({'error': 'Only students can access stats'}, status=403)
    
    # Get completed trips
    completed_trips = Trip.objects.filter(
        student=request.user,
        status='completed'
    )
    
    total_trips = completed_trips.count()
    total_spent = completed_trips.aggregate(models.Sum('total_fare'))['total_fare__sum'] or 0
    
    
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

    active_trip_data = None
    if active_trip:
        active_trip_data = {
            'id': active_trip.id,
            'status': active_trip.status,
            'pickup_address': active_trip.pickup_address,
            'dropoff_address': active_trip.dropoff_address,
            'total_fare': str(active_trip.total_fare),
        }
        if active_trip.driver:
            active_trip_data['driver_name'] = active_trip.driver.get_full_name()
            active_trip_data['driver_phone'] = str(active_trip.driver.phone_number)
    
    context = {
        'title': 'Student Dashboard',
        'user': request.user,
        'active_trip': active_trip,
        'trip_history': trip_history,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
        'total_trips': total_trips,
        'total_spent': total_spent,
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

# @login_required
# def admin_dashboard(request):
#     """Admin dashboard view"""
#     if request.user.role != 'admin':
#         messages.error(request, 'Access denied. Admin only area.')
#         return redirect('bookings:index')
    
#     # Get statistics
#     total_users = User.objects.count()
#     total_students = User.objects.filter(role='student').count()
#     total_drivers = User.objects.filter(role='driver').count()
#     total_trips = Trip.objects.count()
#     completed_trips = Trip.objects.filter(status='completed').count()
#     active_trips = Trip.objects.filter(status__in=['searching', 'accepted', 'arrived', 'ongoing']).count()
    
#     # Calculate revenue
#     total_revenue = Trip.objects.filter(
#         status='completed'
#     ).aggregate(models.Sum('total_fare'))['total_fare__sum'] or 0
    
#     # Recent trips
#     recent_trips = Trip.objects.all().order_by('-requested_at')[:20]
    
#     context = {
#         'title': 'Admin Dashboard',
#         'user': request.user,
#         'total_users': total_users,
#         'total_students': total_students,
#         'total_drivers': total_drivers,
#         'total_trips': total_trips,
#         'completed_trips': completed_trips,
#         'active_trips': active_trips,
#         'total_revenue': total_revenue,
#         'recent_trips': recent_trips,
#     }
#     return render(request, 'admin/dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Admin dashboard with full tracking capabilities"""
    if request.user.role != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin only area.')
        return redirect('bookings:index')
    
    # Get statistics
    total_users = User.objects.count()
    total_students = User.objects.filter(role='student').count()
    total_drivers = User.objects.filter(role='driver').count()
    total_trips = Trip.objects.count()
    
    # Trip status breakdown
    active_trips = Trip.objects.filter(
        status__in=['accepted', 'arrived', 'ongoing']
    ).count()
    
    searching_trips = Trip.objects.filter(status='searching').count()
    completed_trips = Trip.objects.filter(status='completed').count()
    cancelled_trips = Trip.objects.filter(
        status__in=['cancelled_by_student', 'cancelled_by_driver']
    ).count()
    
    # Today's stats
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    
    today_trips = Trip.objects.filter(requested_at__gte=today_start, requested_at__lte=today_end).count()
    today_revenue = Trip.objects.filter(
        completed_at__gte=today_start,
        completed_at__lte=today_end,
        status='completed'
    ).aggregate(Sum('total_fare'))['total_fare__sum'] or 0
    
    # Revenue stats
    total_revenue = Trip.objects.filter(status='completed').aggregate(Sum('total_fare'))['total_fare__sum'] or 0
    
    # Get active trips for tracking
    active_trips_list = Trip.objects.filter(
        status__in=['accepted', 'arrived', 'ongoing']
    ).select_related('student', 'driver', 'driver__driver_profile').order_by('-requested_at')
    
    # Get recent trips
    recent_trips = Trip.objects.all().order_by('-requested_at')[:20]
    
    context = {
        'title': 'Admin Dashboard - UniRide',
        'user': request.user,
        
        # Stats
        'total_users': total_users,
        'total_students': total_students,
        'total_drivers': total_drivers,
        'total_trips': total_trips,
        'active_trips_count': active_trips,
        'searching_trips': searching_trips,
        'completed_trips': completed_trips,
        'cancelled_trips': cancelled_trips,
        'today_trips': today_trips,
        'today_revenue': today_revenue,
        'total_revenue': total_revenue,
        
        # Trip lists
        'active_trips': active_trips_list,
        'recent_trips': recent_trips,
        
        # Google Maps API Key
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    }
    return render(request, 'admins/dashboard.html', context)

@login_required
def admin_trip_detail(request, trip_id):
    """Get detailed trip information for admin"""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    trip = get_object_or_404(Trip, id=trip_id)
    
    # Get driver location if available
    driver_location = None
    if trip.driver and hasattr(trip.driver, 'driver_profile'):
        profile = trip.driver.driver_profile
        if profile.current_latitude and profile.current_longitude:
            driver_location = {
                'latitude': float(profile.current_latitude),
                'longitude': float(profile.current_longitude),
                'last_update': profile.last_location_update.isoformat() if profile.last_location_update else None
            }
    
    # Get trip location history
    locations = list(trip.locations.values('latitude', 'longitude', 'timestamp')[:100])
    
    return JsonResponse({
        'id': trip.id,
        'status': trip.status,
        'status_display': trip.get_status_display(),
        'pickup_address': trip.pickup_address,
        'pickup_latitude': float(trip.pickup_latitude),
        'pickup_longitude': float(trip.pickup_longitude),
        'dropoff_address': trip.dropoff_address,
        'dropoff_latitude': float(trip.dropoff_latitude),
        'dropoff_longitude': float(trip.dropoff_longitude),
        'total_fare': str(trip.total_fare),
        'requested_at': trip.requested_at.isoformat(),
        'accepted_at': trip.accepted_at.isoformat() if trip.accepted_at else None,
        'arrived_at': trip.arrived_at.isoformat() if trip.arrived_at else None,
        'started_at': trip.started_at.isoformat() if trip.started_at else None,
        'completed_at': trip.completed_at.isoformat() if trip.completed_at else None,
        'student': {
            'id': trip.student.id,
            'name': trip.student.get_full_name(),
            'email': trip.student.email,
            'phone': str(trip.student.phone_number),
        },
        'driver': {
            'id': trip.driver.id if trip.driver else None,
            'name': trip.driver.get_full_name() if trip.driver else None,
            'phone': str(trip.driver.phone_number) if trip.driver else None,
            'location': driver_location,
        },
        'location_history': locations,
    })

@login_required
def admin_active_trips(request):
    """API endpoint for admin to get all active trips"""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    active_trips = Trip.objects.filter(
        status__in=['accepted', 'arrived', 'ongoing', 'searching']
    ).select_related('student', 'driver', 'driver__driver_profile').order_by('-requested_at')
    
    trips_data = []
    for trip in active_trips:
        driver_location = None
        if trip.driver and hasattr(trip.driver, 'driver_profile'):
            profile = trip.driver.driver_profile
            if profile.current_latitude and profile.current_longitude:
                driver_location = {
                    'latitude': float(profile.current_latitude),
                    'longitude': float(profile.current_longitude),
                }
        
        trips_data.append({
            'id': trip.id,
            'status': trip.status,
            'status_display': trip.get_status_display(),
            'pickup_latitude': float(trip.pickup_latitude),
            'pickup_longitude': float(trip.pickup_longitude),
            'dropoff_latitude': float(trip.dropoff_latitude),
            'dropoff_longitude': float(trip.dropoff_longitude),
            'total_fare': str(trip.total_fare),
            'student_name': trip.student.get_full_name(),
            'driver_name': trip.driver.get_full_name() if trip.driver else None,
            'driver_location': driver_location,
            'requested_at': trip.requested_at.isoformat(),
        })
    
    return JsonResponse({'trips': trips_data}, status=200)


@login_required
def admin_trip_locations(request, trip_id):
    """API endpoint to get trip location history"""
    if request.user.role != 'admin' and not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    trip = get_object_or_404(Trip, id=trip_id)
    
    # Get location history
    locations = list(trip.locations.values('latitude', 'longitude', 'timestamp')[:100])
    
    # Format locations for map
    location_history = []
    for loc in locations:
        location_history.append({
            'lat': float(loc['latitude']),
            'lng': float(loc['longitude']),
            'timestamp': loc['timestamp'].isoformat() if loc['timestamp'] else None
        })
    
    return JsonResponse({
        'trip_id': trip.id,
        'status': trip.status,
        'locations': location_history,
    }, status=200)


# @login_required
# def trip_list(request):
#     """API endpoint to list trips"""
#     if request.user.role == 'student':
#         trips = Trip.objects.filter(student=request.user)
#     elif request.user.role == 'driver':
#         trips = Trip.objects.filter(driver=request.user)
#     else:
#         trips = Trip.objects.all()
    
#     trips_data = []
#     for trip in trips:
#         trips_data.append({
#             'id': trip.id,
#             'pickup_address': trip.pickup_address,
#             'dropoff_address': trip.dropoff_address,
#             'status': trip.status,
#             'total_fare': str(trip.total_fare),
#             'requested_at': trip.requested_at.isoformat(),
#             'driver_name': trip.driver.get_full_name() if trip.driver else None,
#         })
    
#     return JsonResponse({'trips': trips_data}, status=200)


# @login_required
# def trip_list(request):
#     """API endpoint to list trips with optional status filter"""
#     # Get status filter from query params
#     status_filter = request.GET.get('status')
    
#     # Base queryset based on user role
#     if request.user.role == 'student':
#         trips = Trip.objects.filter(student=request.user)
#     elif request.user.role == 'driver':
#         trips = Trip.objects.filter(driver=request.user)
#     else:
#         trips = Trip.objects.all()
    
#     # Apply status filter if provided
#     if status_filter:
#         trips = trips.filter(status=status_filter)
    
#     trips_data = []
#     for trip in trips:
#         trips_data.append({
#             'id': trip.id,
#             'pickup_address': trip.pickup_address,
#             'dropoff_address': trip.dropoff_address,
#             'status': trip.status,
#             'total_fare': str(trip.total_fare),
#             'requested_at': trip.requested_at.isoformat(),
#             'completed_at': trip.completed_at.isoformat() if trip.completed_at else None,
#             'driver_name': trip.driver.get_full_name() if trip.driver else None,
#             'student_name': trip.student.get_full_name() if trip.student else None,
#         })
    
#     return JsonResponse({'trips': trips_data}, status=200)


@login_required
def trip_list(request):
    """API endpoint to list trips with optional status filter"""
    status_filter = request.GET.get('status')
    
    # Base queryset based on user role
    if request.user.role == 'student':
        trips = Trip.objects.filter(student=request.user)
    elif request.user.role == 'driver':
        # For drivers requesting 'searching' status, show unassigned trips
        if status_filter == 'searching':
            trips = Trip.objects.filter(status='searching', driver__isnull=True)
        else:
            trips = Trip.objects.filter(driver=request.user)
    else:
        trips = Trip.objects.all()
    
    # Apply status filter if provided and not already applied
    if status_filter and status_filter != 'searching':
        trips = trips.filter(status=status_filter)
    
    trips_data = []
    for trip in trips:
        trips_data.append({
            'id': trip.id,
            'pickup_address': trip.pickup_address,
            'dropoff_address': trip.dropoff_address,
            'status': trip.status,
            'total_fare': str(trip.total_fare),
            'requested_at': trip.requested_at.isoformat(),
            'completed_at': trip.completed_at.isoformat() if trip.completed_at else None,
            'driver_name': trip.driver.get_full_name() if trip.driver else None,
            'student_name': trip.student.get_full_name() if trip.student else None,
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

# @login_required
# @csrf_exempt
# def book_ride(request):
#     """API endpoint to book a new ride"""
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Method not allowed'}, status=405)
    
#     if request.user.role != 'student':
#         return JsonResponse({'error': 'Only students can book rides'}, status=403)
    
#     try:
#         data = json.loads(request.body)
        
#         # Create trip
#         trip = Trip.objects.create(
#             student=request.user,
#             pickup_address=data['pickup_address'],
#             pickup_latitude=data['pickup_latitude'],
#             pickup_longitude=data['pickup_longitude'],
#             dropoff_address=data['dropoff_address'],
#             dropoff_latitude=data['dropoff_latitude'],
#             dropoff_longitude=data['dropoff_longitude'],
#             distance_km=data.get('distance_km', 0),
#             duration_minutes=data.get('duration_minutes', 0),
#             status='searching'
#         )
        
#         # Calculate fare
#         trip.calculate_fare()
#         trip.save()
        
#         return JsonResponse({
#             'message': 'Ride booked successfully',
#             'trip_id': trip.id,
#             'trip': {
#                 'id': trip.id,
#                 'total_fare': str(trip.total_fare),
#                 'status': trip.status,
#             }
#         }, status=201)
        
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=400)


# @login_required
# @csrf_exempt
# def book_ride(request):
#     """API endpoint to book a new ride"""
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Method not allowed'}, status=405)
    
#     if request.user.role != 'student':
#         return JsonResponse({'error': 'Only students can book rides'}, status=403)
    
#     try:
#         data = json.loads(request.body)
        
#         # Validate required fields
#         required_fields = ['pickup_address', 'pickup_latitude', 'pickup_longitude', 
#                           'dropoff_address', 'dropoff_latitude', 'dropoff_longitude']
#         for field in required_fields:
#             if field not in data:
#                 return JsonResponse({'error': f'Missing field: {field}'}, status=400)
        
#         # Create trip
#         trip = Trip.objects.create(
#             student=request.user,
#             pickup_address=data['pickup_address'],
#             pickup_latitude=data['pickup_latitude'],
#             pickup_longitude=data['pickup_longitude'],
#             dropoff_address=data['dropoff_address'],
#             dropoff_latitude=data['dropoff_latitude'],
#             dropoff_longitude=data['dropoff_longitude'],
#             distance_km=data.get('distance_km', 0),
#             duration_minutes=data.get('duration_minutes', 0),
#             status='searching'
#         )
        
#         # Calculate fare
#         trip.calculate_fare()
#         trip.save()
        
#         return JsonResponse({
#             'message': 'Ride booked successfully',
#             'trip_id': trip.id,
#             'trip': {
#                 'id': trip.id,
#                 'total_fare': str(trip.total_fare),
#                 'status': trip.status,
#             }
#         }, status=201)
        
#     except json.JSONDecodeError:
#         return JsonResponse({'error': 'Invalid JSON data'}, status=400)
#     except Exception as e:
#         print(f"Booking error: {str(e)}")
#         return JsonResponse({'error': str(e)}, status=400)

@login_required
@csrf_exempt
def book_ride(request):
    """API endpoint to book a new ride"""
    import math
    from users.models import DriverProfile
    
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
        
        # Try to find and assign a nearby driver
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2) * math.sin(dlat/2) + \
                math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
                math.sin(dlon/2) * math.sin(dlon/2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c
        
        # Find available drivers
        driver_profiles = DriverProfile.objects.filter(
            is_available=True,
            current_latitude__isnull=False,
            current_longitude__isnull=False
        ).select_related('user')
        
        closest_driver = None
        min_distance = float('inf')
        
        for profile in driver_profiles:
            distance = haversine(
                float(data['pickup_latitude']), float(data['pickup_longitude']),
                float(profile.current_latitude), float(profile.current_longitude)
            )
            if distance < min_distance and distance <= 5:  # Within 5km
                min_distance = distance
                closest_driver = profile.user
        
        # Assign driver if found
        driver_assigned = False
        if closest_driver:
            trip.driver = closest_driver
            trip.status = 'accepted'
            trip.accepted_at = timezone.now()
            trip.save()
            
            # Mark driver as busy
            closest_driver.is_available = False
            closest_driver.save()
            if hasattr(closest_driver, 'driver_profile'):
                closest_driver.driver_profile.is_available = False
                closest_driver.driver_profile.save()
            
            driver_assigned = True
            
            # Send notification to driver (if WebSocket is set up)
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f'driver_{closest_driver.id}',
                    {
                        'type': 'new_ride_request',
                        'trip_id': trip.id,
                        'pickup_address': trip.pickup_address,
                        'estimated_fare': str(trip.total_fare),
                    }
                )
            except Exception as e:
                print(f"WebSocket notification error: {e}")
        
        return JsonResponse({
            'message': 'Ride booked successfully',
            'trip_id': trip.id,
            'driver_assigned': driver_assigned,
            'driver_name': closest_driver.get_full_name() if closest_driver else None,
            'trip': {
                'id': trip.id,
                'total_fare': str(trip.total_fare),
                'status': trip.status,
            }
        }, status=201)
        
    except Exception as e:
        print(f"Booking error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=400)
# def nearby_drivers(request):
#     """API endpoint to get nearby drivers"""
#     lat = request.GET.get('lat')
#     lng = request.GET.get('lng')
#     radius = request.GET.get('radius', 5)
    
#     if not lat or not lng:
#         return JsonResponse({'drivers': [], 'error': 'Latitude and longitude required'}, status=400)
    
#     # Find available drivers (simplified for now)
#     drivers = User.objects.filter(
#         role='driver',
#         is_available=True,
#         current_latitude__isnull=False
#     )[:10]  # Limit to 10 for now
    
#     drivers_data = []
#     for driver in drivers:
#         drivers_data.append({
#             'id': driver.id,
#             'name': driver.get_full_name(),
#             'rating': 4.5,
#             'vehicle': {
#                 'make': 'Toyota',
#                 'model': 'Camry',
#                 'color': 'White',
#                 'license_plate': 'ABC-123'
#             } if hasattr(driver, 'vehicle') else None,
#             'distance_km': 1.5,
#         })
    
#     return JsonResponse({'drivers': drivers_data}, status=200)


# def nearby_drivers(request):
#     """API endpoint to get nearby drivers"""
#     lat = request.GET.get('lat')
#     lng = request.GET.get('lng')
#     radius = request.GET.get('radius', 5)
    
#     if not lat or not lng:
#         return JsonResponse({'drivers': [], 'error': 'Latitude and longitude required'}, status=400)
    
#     # Find available drivers through DriverProfile
#     from users.models import DriverProfile
    
#     drivers = DriverProfile.objects.filter(
#         is_available=True,
#         current_latitude__isnull=False,
#         current_longitude__isnull=False
#     ).select_related('user')[:10]
    
#     drivers_data = []
#     for driver_profile in drivers:
#         driver = driver_profile.user
#         # Calculate distance (simplified - you can add proper distance calculation)
#         distance_km = 1.5  # Placeholder, calculate actual distance if needed
        
#         drivers_data.append({
#             'id': driver.id,
#             'name': driver.get_full_name(),
#             'rating': float(driver_profile.rating or 0),
#             'vehicle': {
#                 'make': 'Toyota',  # You can get this from Vehicle model
#                 'model': 'Camry',
#                 'color': 'White',
#                 'license_plate': 'ABC-123'
#             } if hasattr(driver, 'vehicle') else None,
#             'distance_km': distance_km,
#         })
    
#     return JsonResponse({'drivers': drivers_data}, status=200)


# bookings/views.py - Complete updated nearby_drivers function

def nearby_drivers(request):
    """API endpoint to get nearby drivers"""
    import math
    from users.models import DriverProfile
    
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    radius = request.GET.get('radius', 5)  # Default 5km radius
    
    if not lat or not lng:
        return JsonResponse({'drivers': [], 'error': 'Latitude and longitude required'}, status=400)
    
    # Convert to float
    try:
        current_lat = float(lat)
        current_lng = float(lng)
        radius_km = float(radius)
    except ValueError:
        return JsonResponse({'drivers': [], 'error': 'Invalid coordinates'}, status=400)
    
    # Haversine formula to calculate distance between two points
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Earth's radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    
    # Get all available drivers with location data
    driver_profiles = DriverProfile.objects.filter(
        is_available=True,
        current_latitude__isnull=False,
        current_longitude__isnull=False
    ).select_related('user')
    
    drivers_data = []
    for profile in driver_profiles:
        # Calculate distance from user to driver
        distance = haversine(
            current_lat, current_lng,
            float(profile.current_latitude), float(profile.current_longitude)
        )
        
        # Only include drivers within the radius
        if distance <= radius_km:
            driver = profile.user
            
            # Get vehicle info if exists
            vehicle_info = None
            if hasattr(driver, 'vehicle'):
                vehicle = driver.vehicle
                vehicle_info = {
                    'make': vehicle.make,
                    'model': vehicle.model,
                    'color': vehicle.color,
                    'license_plate': vehicle.license_plate,
                }
            
            drivers_data.append({
                'id': driver.id,
                'name': driver.get_full_name(),
                'rating': float(profile.rating) if profile.rating else 4.5,
                'vehicle': vehicle_info,
                'distance_km': round(distance, 2),
                'latitude': float(profile.current_latitude),
                'longitude': float(profile.current_longitude),
            })
    
    # Sort by distance (closest first)
    drivers_data.sort(key=lambda x: x['distance_km'])
    
    return JsonResponse({'drivers': drivers_data[:20]}, status=200)  # Limit to 20 drivers


@login_required
@csrf_exempt
def accept_trip(request, trip_id):
    """Driver accepts a trip"""
    if request.user.role != 'driver':
        return JsonResponse({'error': 'Only drivers can accept trips'}, status=403)
    
    trip = get_object_or_404(Trip, id=trip_id)
    
    if trip.status != 'searching':
        return JsonResponse({'error': 'Trip is no longer available'}, status=400)
    
    trip.driver = request.user
    trip.status = 'accepted'
    trip.accepted_at = timezone.now()
    trip.save()
    
    # Update driver availability
    request.user.is_available = False
    request.user.save()
    
    return JsonResponse({
        'message': 'Trip accepted successfully',
        'trip_id': trip.id,
        'status': trip.status
    })

@login_required
@csrf_exempt
def start_trip(request, trip_id):
    """Driver starts the trip"""
    if request.user.role != 'driver':
        return JsonResponse({'error': 'Only drivers can start trips'}, status=403)
    
    trip = get_object_or_404(Trip, id=trip_id, driver=request.user)
    
    if trip.status != 'arrived':
        return JsonResponse({'error': 'Cannot start trip yet. Must arrive at pickup first.'}, status=400)
    
    trip.status = 'ongoing'
    trip.started_at = timezone.now()
    trip.save()
    
    return JsonResponse({
        'message': 'Trip started',
        'trip_id': trip.id,
        'status': trip.status
    })

# @login_required
# @csrf_exempt
# def complete_trip(request, trip_id):
#     """Driver completes the trip"""
#     if request.user.role != 'driver':
#         return JsonResponse({'error': 'Only drivers can complete trips'}, status=403)
    
#     trip = get_object_or_404(Trip, id=trip_id, driver=request.user)
    
#     if trip.status != 'ongoing':
#         return JsonResponse({'error': 'Trip not in progress'}, status=400)
    
#     trip.status = 'completed'
#     trip.completed_at = timezone.now()
#     trip.is_paid = True
#     trip.save()
    
#     # Update driver availability back to available
#     request.user.is_available = True
#     request.user.save()
    
#     return JsonResponse({
#         'message': 'Trip completed',
#         'trip_id': trip.id,
#         'fare': str(trip.total_fare)
#     })


@login_required
@csrf_exempt
def complete_trip(request, trip_id):
    """Driver completes the trip"""
    if request.user.role != 'driver':
        return JsonResponse({'error': 'Only drivers can complete trips'}, status=403)
    
    trip = get_object_or_404(Trip, id=trip_id, driver=request.user)
    
    # Allow completion from any status (for testing/development)
    # In production, you might want to restrict to only 'ongoing'
    if trip.status not in ['ongoing', 'arrived', 'accepted']:
        return JsonResponse({'error': f'Trip cannot be completed from status: {trip.status}'}, status=400)
    
    # Update trip
    trip.status = 'completed'
    trip.completed_at = timezone.now()
    trip.is_paid = True
    trip.save()
    
    # Update driver availability back to available
    request.user.is_available = True
    request.user.save()
    
    # Update driver profile if exists
    if hasattr(request.user, 'driver_profile'):
        profile = request.user.driver_profile
        profile.is_available = True
        profile.total_trips += 1
        profile.total_earnings += trip.total_fare
        profile.save()
    
    # Update student profile
    if hasattr(trip.student, 'student_profile'):
        student_profile = trip.student.student_profile
        student_profile.total_trips += 1
        student_profile.total_spent += trip.total_fare
        student_profile.save()
    
    # Send notification via WebSocket
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        
        # Notify student
        async_to_sync(channel_layer.group_send)(
            f'notifications_{trip.student.id}',
            {
                'type': 'send_notification',
                'title': 'Trip Completed',
                'message': f'Your trip has been completed. Thank you for riding with us!',
                'notification_type': 'ride_completed',
            }
        )
        
        # Notify driver (if they have notifications)
        async_to_sync(channel_layer.group_send)(
            f'notifications_{request.user.id}',
            {
                'type': 'send_notification',
                'title': 'Trip Completed',
                'message': f'Trip #{trip.id} completed. You earned ₦{trip.total_fare}',
                'notification_type': 'ride_completed',
            }
        )
    except Exception as e:
        print(f"WebSocket notification error: {e}")
    
    return JsonResponse({
        'message': 'Trip completed successfully',
        'trip_id': trip.id,
        'status': trip.status,
        'fare': str(trip.total_fare)
    }, status=200)

@login_required
def driver_current_trip(request):
    """Get driver's current active trip"""
    if request.user.role != 'driver':
        return JsonResponse({'error': 'Only drivers'}, status=403)
    
    current_trip = Trip.objects.filter(
        driver=request.user,
        status__in=['accepted', 'arrived', 'ongoing']
    ).first()
    
    if current_trip:
        return JsonResponse({
            'id': current_trip.id,
            'pickup_address': current_trip.pickup_address,
            'pickup_latitude': str(current_trip.pickup_latitude),
            'pickup_longitude': str(current_trip.pickup_longitude),
            'dropoff_address': current_trip.dropoff_address,
            'dropoff_latitude': str(current_trip.dropoff_latitude),
            'dropoff_longitude': str(current_trip.dropoff_longitude),
            'status': current_trip.status,
            'fare': str(current_trip.total_fare),
            'student_name': current_trip.student.get_full_name(),
            'student_phone': str(current_trip.student.phone_number),
        })
    
    return JsonResponse({'message': 'No active trip'}, status=404)

@login_required
@csrf_exempt
def update_driver_status(request):
    """Update driver's online/offline status"""
    if request.user.role != 'driver':
        return JsonResponse({'error': 'Only drivers can update status'}, status=403)
    
    try:
        data = json.loads(request.body)
        is_available = data.get('is_available', False)
        
        request.user.is_available = is_available
        request.user.save()
        
        # Also update driver profile if it exists
        if hasattr(request.user, 'driver_profile'):
            profile = request.user.driver_profile
            profile.is_available = is_available
            profile.save()
        
        return JsonResponse({
            'message': f'Status updated to {"online" if is_available else "offline"}',
            'is_available': is_available
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@csrf_exempt
def arrive_at_pickup(request, trip_id):
    """Driver arrives at pickup location"""
    if request.user.role != 'driver':
        return JsonResponse({'error': 'Only drivers can update arrival'}, status=403)
    
    trip = get_object_or_404(Trip, id=trip_id, driver=request.user)
    
    if trip.status != 'accepted':
        return JsonResponse({'error': 'Trip must be accepted first'}, status=400)
    
    trip.status = 'arrived'
    trip.arrived_at = timezone.now()
    trip.save()
    
    return JsonResponse({
        'message': 'Arrived at pickup location',
        'trip_id': trip.id,
        'status': trip.status
    })

# @login_required
# @csrf_exempt
# def update_driver_location(request):
#     """Update driver's current location (API endpoint)"""
#     if request.user.role != 'driver':
#         return JsonResponse({'error': 'Only drivers can update location'}, status=403)
    
#     try:
#         data = json.loads(request.body)
#         latitude = data.get('latitude')
#         longitude = data.get('longitude')
        
#         if not latitude or not longitude:
#             return JsonResponse({'error': 'Latitude and longitude required'}, status=400)
        
#         # Update driver profile
#         if hasattr(request.user, 'driver_profile'):
#             profile = request.user.driver_profile
#             profile.current_latitude = latitude
#             profile.current_longitude = longitude
#             profile.last_location_update = timezone.now()
#             profile.save()
        
#         # Also update the user model fields
#         request.user.current_latitude = latitude
#         request.user.current_longitude = longitude
#         request.user.save()
        
#         return JsonResponse({
#             'message': 'Location updated',
#             'latitude': latitude,
#             'longitude': longitude
#         })
        
#     except json.JSONDecodeError:
#         return JsonResponse({'error': 'Invalid JSON'}, status=400)
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def update_driver_location(request):
    """Update driver's current location (API endpoint)"""
    if request.user.role != 'driver':
        return JsonResponse({'error': 'Only drivers can update location'}, status=403)
    
    try:
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not latitude or not longitude:
            return JsonResponse({'error': 'Latitude and longitude required'}, status=400)
        
        # Update driver profile
        if hasattr(request.user, 'driver_profile'):
            profile = request.user.driver_profile
            profile.current_latitude = latitude
            profile.current_longitude = longitude
            profile.last_location_update = timezone.now()
            profile.save()
            print(f"Updated driver {request.user.email} location: {latitude}, {longitude}")
        else:
            return JsonResponse({'error': 'Driver profile not found'}, status=400)
        
        return JsonResponse({
            'message': 'Location updated',
            'latitude': latitude,
            'longitude': longitude
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"Location update error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_driver_location(request, driver_id):
    """Get driver's current location (for students tracking)"""
    driver = get_object_or_404(User, id=driver_id, role='driver')
    
    location_data = {
        'driver_id': driver.id,
        'name': driver.get_full_name(),
        'latitude': None,
        'longitude': None,
        'last_update': None
    }
    
    if hasattr(driver, 'driver_profile'):
        profile = driver.driver_profile
        location_data['latitude'] = str(profile.current_latitude) if profile.current_latitude else None
        location_data['longitude'] = str(profile.current_longitude) if profile.current_longitude else None
        location_data['last_update'] = profile.last_location_update.isoformat() if profile.last_location_update else None
    
    # Also check user model fields
    if not location_data['latitude'] and driver.current_latitude:
        location_data['latitude'] = str(driver.current_latitude)
        location_data['longitude'] = str(driver.current_longitude)
    
    return JsonResponse(location_data)


@login_required
def profile_page(request):
    """User profile page"""
    return render(request, 'profile.html', {
        'title': 'My Profile',
        'user': request.user
    })

@login_required
def trip_history_page(request):
    """Trip history page"""
    return render(request, 'trip_history.html', {
        'title': 'Trip History',
        'user': request.user
    })

@login_required
def driver_earnings(request):
    """API endpoint for driver earnings statistics"""
    if request.user.role != 'driver':
        return JsonResponse({'error': 'Only drivers can access earnings'}, status=403)
    
    from django.utils import timezone
    from datetime import timedelta
    
    # Get today's date range
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # Get all completed trips for this driver
    completed_trips = Trip.objects.filter(
        driver=request.user,
        status='completed'
    )
    
    # Calculate today's earnings
    today_trips = completed_trips.filter(completed_at__gte=today_start, completed_at__lt=today_end)
    today_earnings = today_trips.aggregate(models.Sum('total_fare'))['total_fare__sum'] or 0
    
    # Calculate total earnings
    total_earnings = completed_trips.aggregate(models.Sum('total_fare'))['total_fare__sum'] or 0
    
    # Get completed trips count
    completed_count = completed_trips.count()
    
    # Get driver rating
    rating = 0
    if hasattr(request.user, 'driver_profile'):
        rating = float(request.user.driver_profile.rating or 0)
    
    return JsonResponse({
        'total': float(total_earnings),
        'today': float(today_earnings),
        'completed_trips': completed_count,
        'rating': rating,
    }, status=200)


@login_required
def student_stats(request):
    """API endpoint for student statistics"""
    if request.user.role != 'student':
        return JsonResponse({'error': 'Only students can access stats'}, status=403)
    
    # Get completed trips
    completed_trips = Trip.objects.filter(
        student=request.user,
        status='completed'
    )
    
    total_trips = completed_trips.count()
    total_spent = completed_trips.aggregate(models.Sum('total_fare'))['total_fare__sum'] or 0
    
    # Get active trip
    active_trip = Trip.objects.filter(
        student=request.user,
        status__in=['searching', 'accepted', 'arrived', 'ongoing']
    ).first()
    
    active_trip_data = None
    if active_trip:
        active_trip_data = {
            'id': active_trip.id,
            'status': active_trip.status,
            'pickup_address': active_trip.pickup_address,
            'dropoff_address': active_trip.dropoff_address,
            'total_fare': str(active_trip.total_fare),
        }
        if active_trip.driver:
            active_trip_data['driver_name'] = active_trip.driver.get_full_name()
            active_trip_data['driver_phone'] = str(active_trip.driver.phone_number)
    
    return JsonResponse({
        'total_trips': total_trips,
        'total_spent': float(total_spent),
        'wallet_balance': float(request.user.wallet_balance),
        'active_trip': active_trip_data,
    }, status=200)


@login_required
def student_active_trip(request):
    """Get student's active trip"""
    if request.user.role != 'student':
        return JsonResponse({'error': 'Only students'}, status=403)
    
    active_trip = Trip.objects.filter(
        student=request.user,
        status__in=['searching', 'accepted', 'arrived', 'ongoing']
    ).first()
    
    if active_trip:
        return JsonResponse({
            'id': active_trip.id,
            'pickup_address': active_trip.pickup_address,
            'dropoff_address': active_trip.dropoff_address,
            'status': active_trip.status,
            'total_fare': str(active_trip.total_fare),
            'driver_name': active_trip.driver.get_full_name() if active_trip.driver else None,
            'driver_phone': str(active_trip.driver.phone_number) if active_trip.driver else None,
        })
    
    return JsonResponse({'message': 'No active trip'}, status=404)



# bookings/views.py - Add/Update these functions

@login_required
def get_available_rides(request):
    """Get all available rides for drivers"""
    if request.user.role != 'driver':
        return JsonResponse({'error': 'Only drivers can view rides'}, status=403)
    
    # Get all trips that are searching for drivers
    available_trips = Trip.objects.filter(
        status='searching'
    ).select_related('student').order_by('-requested_at')
    
    trips_data = []
    for trip in available_trips:
        trips_data.append({
            'id': trip.id,
            'pickup_address': trip.pickup_address,
            'dropoff_address': trip.dropoff_address,
            'fare': str(trip.total_fare),
            'distance': str(trip.distance_km),
            'duration': trip.duration_minutes,
            'requested_at': trip.requested_at.isoformat(),
            'student_name': trip.student.get_full_name(),
            'student_rating': trip.student.get_average_rating(),
        })
    
    return JsonResponse({'rides': trips_data}, status=200)

@login_required
@csrf_exempt
def accept_ride(request, trip_id):
    """Driver accepts a ride"""
    if request.user.role != 'driver':
        return JsonResponse({'error': 'Only drivers can accept rides'}, status=403)
    
    trip = get_object_or_404(Trip, id=trip_id)
    
    if trip.status != 'searching':
        return JsonResponse({'error': 'This ride is no longer available'}, status=400)
    
    # Check if driver already has an active trip
    active_trip = Trip.objects.filter(
        driver=request.user,
        status__in=['accepted', 'arrived', 'ongoing']
    ).exists()
    
    if active_trip:
        return JsonResponse({'error': 'You already have an active trip'}, status=400)
    
    # Accept the trip
    trip.driver = request.user
    trip.status = 'accepted'
    trip.accepted_at = timezone.now()
    trip.save()
    
    # Update driver availability
    request.user.is_available = False
    request.user.save()
    if hasattr(request.user, 'driver_profile'):
        request.user.driver_profile.is_available = False
        request.user.driver_profile.save()
    
    return JsonResponse({
        'message': 'Ride accepted successfully',
        'trip_id': trip.id,
        'status': trip.status,
        'pickup_address': trip.pickup_address,
        'dropoff_address': trip.dropoff_address,
        'student_name': trip.student.get_full_name(),
        'student_phone': str(trip.student.phone_number),
        'fare': str(trip.total_fare),
    }, status=200)

@login_required
@csrf_exempt
def driver_arrived(request, trip_id):
    """Driver arrives at pickup location"""
    if request.user.role != 'driver':
        return JsonResponse({'error': 'Only drivers can update arrival'}, status=403)
    
    trip = get_object_or_404(Trip, id=trip_id, driver=request.user)
    
    if trip.status != 'accepted':
        return JsonResponse({'error': 'Trip must be accepted first'}, status=400)
    
    trip.status = 'arrived'
    trip.arrived_at = timezone.now()
    trip.save()
    
    # Send notification to student (via WebSocket)
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'student_{trip.student.id}',
            {
                'type': 'driver_status',
                'status': 'arrived',
                'driver_name': request.user.get_full_name(),
                'message': 'Your driver has arrived at the pickup location!'
            }
        )
    except Exception as e:
        print(f"WebSocket error: {e}")
    
    return JsonResponse({
        'message': 'Arrived at pickup location',
        'trip_id': trip.id,
        'status': trip.status
    }, status=200)

@login_required
def get_active_trip_student(request):
    """Get active trip for student with driver details"""
    if request.user.role != 'student':
        return JsonResponse({'error': 'Only students'}, status=403)
    
    active_trip = Trip.objects.filter(
        student=request.user,
        status__in=['accepted', 'arrived', 'ongoing']
    ).select_related('driver', 'driver__driver_profile').first()
    
    if active_trip:
        driver_data = None
        if active_trip.driver:
            driver_data = {
                'id': active_trip.driver.id,
                'name': active_trip.driver.get_full_name(),
                'phone': str(active_trip.driver.phone_number),
                'rating': active_trip.driver.get_average_rating(),
                'latitude': None,
                'longitude': None,
            }
            # Get driver's current location if available
            if hasattr(active_trip.driver, 'driver_profile'):
                profile = active_trip.driver.driver_profile
                driver_data['latitude'] = float(profile.current_latitude) if profile.current_latitude else None
                driver_data['longitude'] = float(profile.current_longitude) if profile.current_longitude else None
        
        return JsonResponse({
            'id': active_trip.id,
            'pickup_address': active_trip.pickup_address,
            'pickup_latitude': float(active_trip.pickup_latitude),
            'pickup_longitude': float(active_trip.pickup_longitude),
            'dropoff_address': active_trip.dropoff_address,
            'dropoff_latitude': float(active_trip.dropoff_latitude),
            'dropoff_longitude': float(active_trip.dropoff_longitude),
            'status': active_trip.status,
            'total_fare': str(active_trip.total_fare),
            'driver': driver_data,
        })
    
    return JsonResponse({'has_active_trip': False}, status=200)

# @login_required
# def get_driver_active_trip(request):
#     """Get active trip for driver with student details"""
#     if request.user.role != 'driver':
#         return JsonResponse({'error': 'Only drivers'}, status=403)
    
#     active_trip = Trip.objects.filter(
#         driver=request.user,
#         status__in=['accepted', 'arrived', 'ongoing']
#     ).select_related('student').first()
    
#     if active_trip:
#         return JsonResponse({
#             'id': active_trip.id,
#             'pickup_address': active_trip.pickup_address,
#             'pickup_latitude': float(active_trip.pickup_latitude),
#             'pickup_longitude': float(active_trip.pickup_longitude),
#             'dropoff_address': active_trip.dropoff_address,
#             'dropoff_latitude': float(active_trip.dropoff_latitude),
#             'dropoff_longitude': float(active_trip.dropoff_longitude),
#             'status': active_trip.status,
#             'total_fare': str(active_trip.total_fare),
#             'student_name': active_trip.student.get_full_name(),
#             'student_phone': str(active_trip.student.phone_number),
#         })
    
#     return JsonResponse({'has_active_trip': False}, status=200)



@login_required
def get_driver_active_trip(request):
    """Get driver's current active trip"""
    if request.user.role != 'driver':
        return JsonResponse({'error': 'Only drivers can access this'}, status=403)
    
    # Look for any non-completed trip
    current_trip = Trip.objects.filter(
        driver=request.user
    ).exclude(
        status__in=['completed', 'cancelled_by_driver', 'cancelled_by_student']
    ).select_related('student').first()
    
    if current_trip:
        return JsonResponse({
            'id': current_trip.id,
            'pickup_address': current_trip.pickup_address,
            'pickup_latitude': float(current_trip.pickup_latitude),
            'pickup_longitude': float(current_trip.pickup_longitude),
            'dropoff_address': current_trip.dropoff_address,
            'dropoff_latitude': float(current_trip.dropoff_latitude),
            'dropoff_longitude': float(current_trip.dropoff_longitude),
            'status': current_trip.status,
            'total_fare': str(current_trip.total_fare),
            'student_name': current_trip.student.get_full_name(),
            'student_phone': str(current_trip.student.phone_number),
        })
    
    return JsonResponse({'has_active_trip': False}, status=404)

@csrf_exempt
def health_check(request):
    # You can add a database check here later, but for now, just a simple response
    return JsonResponse({"status": "ok"})