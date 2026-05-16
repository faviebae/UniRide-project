from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

class Trip(models.Model):
    """Main Trip/Booking model"""
    
    STATUS_CHOICES = [
        ('requesting', 'Requesting Driver'),
        ('searching', 'Searching for Driver'),
        ('accepted', 'Driver Accepted'),
        ('arrived', 'Driver Arrived'),
        ('ongoing', 'Trip in Progress'),
        ('completed', 'Completed'),
        ('cancelled_by_student', 'Cancelled by Student'),
        ('cancelled_by_driver', 'Cancelled by Driver'),
        ('no_driver_found', 'No Driver Found'),
    ]
    
    PAYMENT_METHODS = [
        ('wallet', 'Wallet Balance'),
        ('cash', 'Cash'),
        ('card', 'Card'),
    ]
    
    # Relationships
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='trips_as_student'
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='trips_as_driver'
    )
    
    # Location details (stored as text for simplicity)
    pickup_address = models.TextField()
    pickup_latitude = models.DecimalField(max_digits=10, decimal_places=7)
    pickup_longitude = models.DecimalField(max_digits=10, decimal_places=7)
    
    dropoff_address = models.TextField()
    dropoff_latitude = models.DecimalField(max_digits=10, decimal_places=7)
    dropoff_longitude = models.DecimalField(max_digits=10, decimal_places=7)
    
    # Trip details
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duration_minutes = models.IntegerField(default=0)
    
    # Pricing
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, default=500)
    distance_fare = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    time_fare = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=50)
    total_fare = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Payment
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='wallet')
    is_paid = models.BooleanField(default=False)
    
    # Status
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='requesting')
    cancellation_reason = models.TextField(blank=True)
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['driver', 'status']),
            models.Index(fields=['status', 'requested_at']),
        ]
    
    def __str__(self):
        return f"Trip #{self.id} - {self.student.email} to {self.dropoff_address[:30]}"
    
    def calculate_fare(self):
        """Calculate total fare based on distance and duration"""
        from django.conf import settings
        
        config = getattr(settings, 'RIDE_CONFIG', {
            'BASE_FARE': 500,
            'PER_KM_RATE': 150,
            'PER_MINUTE_RATE': 20,
            'SERVICE_FEE': 50,
        })
        
        self.distance_fare = self.distance_km * config['PER_KM_RATE']
        self.time_fare = self.duration_minutes * config['PER_MINUTE_RATE']
        self.total_fare = (
            config['BASE_FARE'] + 
            self.distance_fare + 
            self.time_fare + 
            config['SERVICE_FEE']
        )
        return self.total_fare
    
    def accept(self, driver):
        """Accept the trip by a driver"""
        self.driver = driver
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()
    
    def arrive(self):
        """Driver arrived at pickup"""
        self.status = 'arrived'
        self.arrived_at = timezone.now()
        self.save()
    
    def start(self):
        """Start the trip"""
        self.status = 'ongoing'
        self.started_at = timezone.now()
        self.save()
    
    def complete(self):
        """Complete the trip"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.is_paid = True
        self.save()
    
    def cancel(self, cancelled_by, reason=''):
        """Cancel the trip"""
        if cancelled_by == 'student':
            self.status = 'cancelled_by_student'
        elif cancelled_by == 'driver':
            self.status = 'cancelled_by_driver'
        
        self.cancellation_reason = reason
        self.cancelled_at = timezone.now()
        self.save()

class TripLocation(models.Model):
    """Real-time location updates during trip"""
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='locations')
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Location for Trip #{self.trip.id} at {self.timestamp}"