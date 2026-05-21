from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterVehicleView.as_view(), name='register_vehicle'),
    path('update/', views.UpdateVehicleView.as_view(), name='update_vehicle'),
    path('my-vehicle/', views.GetVehicleView.as_view(), name='my_vehicle'),
]