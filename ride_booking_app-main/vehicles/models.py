from django.db import models
from django.conf import settings

class Vehicle(models.Model):
    driver = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='vehicle'
    )
    
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    color = models.CharField(max_length=30)
    license_plate = models.CharField(max_length=20, unique=True)
    
    # Vehicle photos
    photo = models.ImageField(upload_to='vehicles/', null=True, blank=True)
    
    # Status
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.make} {self.model} - {self.license_plate}"