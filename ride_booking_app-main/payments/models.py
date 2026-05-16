from django.db import models
from django.conf import settings

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    trip = models.OneToOneField('bookings.Trip', on_delete=models.CASCADE, related_name='payment')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments_made')
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments_received')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    driver_earning = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    payment_method = models.CharField(max_length=20)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment for Trip #{self.trip.id} - {self.amount}"