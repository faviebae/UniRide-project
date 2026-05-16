from django.contrib import admin
from .models import Trip, TripLocation

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'driver', 'status', 'total_fare', 'requested_at']
    list_filter = ['status', 'payment_method', 'requested_at']
    search_fields = ['student__email', 'driver__email', 'pickup_address', 'dropoff_address']
    readonly_fields = ['requested_at', 'accepted_at', 'arrived_at', 'started_at', 'completed_at']
    
    fieldsets = (
        ('Trip Info', {
            'fields': ('student', 'driver', 'status')
        }),
        ('Locations', {
            'fields': ('pickup_address', 'pickup_latitude', 'pickup_longitude', 
                      'dropoff_address', 'dropoff_latitude', 'dropoff_longitude')
        }),
        ('Trip Details', {
            'fields': ('distance_km', 'duration_minutes')
        }),
        ('Pricing', {
            'fields': ('base_fare', 'distance_fare', 'time_fare', 'service_fee', 'total_fare', 'payment_method', 'is_paid')
        }),
        ('Timestamps', {
            'fields': ('requested_at', 'accepted_at', 'arrived_at', 'started_at', 'completed_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(TripLocation)
class TripLocationAdmin(admin.ModelAdmin):
    list_display = ['trip', 'latitude', 'longitude', 'timestamp']
    list_filter = ['timestamp']