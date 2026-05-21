# from django.contrib import admin
# from django.urls import path, include
# from django.conf import settings
# from django.conf.urls.static import static
# from . import views

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', views.index, name='index'),
#     path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
#     path('driver/dashboard/', views.driver_dashboard, name='driver_dashboard'),
#     path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
#     # API URLs
#     path('api/', include('api.urls')),  # Your API endpoints
# ]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


from django.urls import path
from . import views

app_name = 'bookings'  # This helps with URL namespacing

urlpatterns = [
    # Frontend pages
    path('', views.index, name='index'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('driver/dashboard/', views.driver_dashboard, name='driver_dashboard'),
    # path('admins/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('profile/', views.profile_page, name='profile_page'),
    # path('register/', views.registration_page, name='registration_page'),  # Add this
    # path('login/', views.login_page, name='login_page'),
    
    # Trip management
    path('trips/', views.trip_list, name='trip_list'),
    path('trips/<int:trip_id>/', views.trip_detail, name='trip_detail'),
    path('trips/<int:trip_id>/cancel/', views.cancel_trip, name='cancel_trip'),
    
    # Booking API endpoints (if you have them)
    path('book/', views.book_ride, name='book_ride_api'),
    path('nearby-drivers/', views.nearby_drivers, name='nearby_drivers_api'),
    path('student/active-trip/', views.student_active_trip, name='student_active_trip'),

    path('driver/location/', views.update_driver_location, name='update_driver_location'),
    path('driver/location/<int:driver_id>/', views.get_driver_location, name='get_driver_location'),
    path('trips/history/', views.trip_history_page, name='trip_history_page'),

    path('trips/<int:trip_id>/accept/', views.accept_trip, name='accept_trip'),
    path('trips/<int:trip_id>/arrive/', views.arrive_at_pickup, name='arrive_trip'),
    path('trips/<int:trip_id>/start/', views.start_trip, name='start_trip'),
    path('trips/<int:trip_id>/complete/', views.complete_trip, name='complete_trip'),
    path('driver/current-trip/', views.driver_current_trip, name='driver_current_trip'),
    
    # Driver availability
    path('driver/status/', views.update_driver_status, name='driver_status'),
    path('driver/earnings/', views.driver_earnings, name='driver_earnings'),
    path('student/stats/', views.student_stats, name='student_stats'),
    path('driver/available-rides/', views.get_available_rides, name='available_rides'),
    path('driver/accept-ride/<int:trip_id>/', views.accept_ride, name='accept_ride'),
    path('driver/arrived/<int:trip_id>/', views.driver_arrived, name='driver_arrived'),
    path('driver/active-trip/', views.get_driver_active_trip, name='driver_active_trip'),
    
    # Student endpoints
    path('student/active-trip/', views.get_active_trip_student, name='student_active_trip'),
    path('admins/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admins/trip/<int:trip_id>/', views.admin_trip_detail, name='admin_trip_detail'),
    path('admins/trips/active/', views.admin_active_trips, name='admin_active_trips'),
    path('admins/trip/<int:trip_id>/locations/', views.admin_trip_locations, name='admin_trip_locations'),
]



