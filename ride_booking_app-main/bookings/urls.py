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
    path('admins/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    # path('register/', views.registration_page, name='registration_page'),  # Add this
    # path('login/', views.login_page, name='login_page'),
    
    # Trip management
    path('trips/', views.trip_list, name='trip_list'),
    path('trips/<int:trip_id>/', views.trip_detail, name='trip_detail'),
    path('trips/<int:trip_id>/cancel/', views.cancel_trip, name='cancel_trip'),
    
    # Booking API endpoints (if you have them)
    path('book/', views.book_ride, name='book_ride_api'),
    path('nearby-drivers/', views.nearby_drivers, name='nearby_drivers_api'),
]



