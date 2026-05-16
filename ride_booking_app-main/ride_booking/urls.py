# from django.contrib import admin
# from django.urls import path, include
# from rest_framework_simplejwt.views import TokenRefreshView
# from users.views import RegisterView, LoginView, UserProfileView

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('api/register/', RegisterView.as_view(), name='register'),
#     path('api/login/', LoginView.as_view(), name='login'),
#     path('api/profile/', UserProfileView.as_view(), name='profile'),
#     path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
# ]


from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import RegisterView, LoginView, UserProfileView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Authentication APIs
    # path('register/', RegisterView.as_view(), name='register'),
    # path('login/', LoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Include app URLs
    path('', include('bookings.urls')),  # This includes all booking app URLs
    path('', include('users.urls')),  # If you have users app URLs
    # path('vehicles/', include('vehicles.urls')),  # If you have vehicles app URLs
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)