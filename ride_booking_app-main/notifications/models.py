from django.db import models
from django.conf import settings
from django.utils import timezone

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('ride_request', 'New Ride Request'),
        ('ride_accepted', 'Ride Accepted'),
        ('ride_cancelled', 'Ride Cancelled'),
        ('driver_arrived', 'Driver Arrived'),
        ('ride_started', 'Ride Started'),
        ('ride_completed', 'Ride Completed'),
        ('payment_received', 'Payment Received'),
        ('system', 'System Notification'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_trip_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"