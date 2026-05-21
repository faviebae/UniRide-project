from django.contrib import admin
from .models import Vehicle

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['id', 'driver_name', 'make', 'model', 'year', 'color', 'license_plate', 'is_approved']
    list_filter = ['is_approved', 'make', 'year']
    search_fields = ['make', 'model', 'license_plate', 'driver__email', 'driver__first_name', 'driver__last_name']
    readonly_fields = ['created_at']
    list_editable = ['is_approved']
    
    def driver_name(self, obj):
        return obj.driver.get_full_name() if obj.driver else 'No driver'
    driver_name.short_description = 'Driver'
    
    fieldsets = (
        ('Driver Information', {
            'fields': ('driver',)
        }),
        ('Vehicle Details', {
            'fields': ('make', 'model', 'year', 'color', 'license_plate', 'photo')
        }),
        ('Status', {
            'fields': ('is_approved',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )