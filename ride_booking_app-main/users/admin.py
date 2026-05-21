from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import DriverProfile, StudentProfile, User

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'get_full_name', 'role', 'is_active', 'wallet_balance')
    list_filter = ('role', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'avatar')}),
        ('Role & Status', {'fields': ('role', 'is_active', 'wallet_balance')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'role', 'password1', 'password2'),
        }),
    )

@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'license_number', 'is_available', 'total_trips', 'total_earnings', 'rating']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'license_number']
    readonly_fields = ['total_trips', 'total_earnings', 'rating', 'created_at', 'updated_at']

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'student_id', 'institution', 'total_trips', 'total_spent']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'student_id']
    readonly_fields = ['total_trips', 'total_spent', 'created_at', 'updated_at']

admin.site.register(User, CustomUserAdmin)