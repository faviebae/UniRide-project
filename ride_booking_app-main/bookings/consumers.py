# bookings/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Trip, TripLocation
from users.models import DriverProfile, User
from django.utils import timezone

class TripTrackingConsumer(AsyncWebsocketConsumer):
    """Handle real-time trip tracking for students"""
    
    async def connect(self):
        self.trip_id = self.scope['url_route']['kwargs']['trip_id']
        self.trip_group_name = f'trip_{self.trip_id}'
        
        # Check if user is authorized (student or driver of this trip)
        user = self.scope['user']
        trip = await self.get_trip()
        
        if not user.is_authenticated:
            await self.close()
        elif user.role == 'student' and trip.student_id != user.id:
            await self.close()
        elif user.role == 'driver' and trip.driver_id != user.id:
            await self.close()
        else:
            # Join trip group
            await self.channel_layer.group_add(
                self.trip_group_name,
                self.channel_name
            )
            await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.trip_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive location updates from drivers"""
        data = json.loads(text_data)
        
        if data.get('type') == 'location_update':
            # Save location to database
            await self.save_trip_location(
                self.trip_id,
                data['latitude'],
                data['longitude']
            )
            
            # Broadcast to all connected clients (students tracking this trip)
            await self.channel_layer.group_send(
                self.trip_group_name,
                {
                    'type': 'driver_location',
                    'latitude': data['latitude'],
                    'longitude': data['longitude'],
                    'heading': data.get('heading'),
                    'speed': data.get('speed'),
                }
            )
        
        elif data.get('type') == 'status_update':
            # Update trip status
            await self.update_trip_status(self.trip_id, data['status'])
            
            await self.channel_layer.group_send(
                self.trip_group_name,
                {
                    'type': 'trip_status',
                    'status': data['status'],
                    'message': data.get('message', ''),
                }
            )
    
    async def driver_location(self, event):
        """Send driver location to student"""
        await self.send(text_data=json.dumps({
            'type': 'driver_location',
            'latitude': event['latitude'],
            'longitude': event['longitude'],
            'heading': event.get('heading'),
            'speed': event.get('speed'),
        }))
    
    # async def trip_status(self, event):
    #     """Send trip status update"""
    #     await self.send(text_data=json.dumps({
    #         'type': 'status_update',
    #         'status': event['status'],
    #         'message': event.get('message', ''),
    #     }))

    async def trip_status(self, event):
        """Send trip status update to student"""
        await self.send(text_data=json.dumps({
            'type': 'notification',  # Changed to generic notification
            'title': self.get_notification_title(event['status']),
            'message': event.get('message', ''),
            'status': event['status'],
        }))
    
    def get_notification_title(self, status):
        titles = {
            'accepted': 'Driver Accepted',
            'arrived': 'Driver Has Arrived', 
            'ongoing': 'Trip Started',
            'completed': 'Trip Completed',
            'cancelled': 'Trip Cancelled'
        }
        return titles.get(status, 'Status Update')
    
    @database_sync_to_async
    def get_trip(self):
        return Trip.objects.get(id=self.trip_id)
    
    @database_sync_to_async
    def save_trip_location(self, trip_id, lat, lng):
        TripLocation.objects.create(
            trip_id=trip_id,
            latitude=lat,
            longitude=lng
        )
    
    @database_sync_to_async
    def update_trip_status(self, trip_id, status):
        trip = Trip.objects.get(id=trip_id)
        trip.status = status
        if status == 'accepted':
            trip.accepted_at = timezone.now()
        elif status == 'ongoing':
            trip.started_at = timezone.now()
        elif status == 'completed':
            trip.completed_at = timezone.now()
        trip.save()
    
    async def trip_status(self, event):
        """Send trip status update to student"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'title': self.get_notification_title(event['status']),
            'message': event.get('message', ''),
            'status': event['status'],
        }))
    
    def get_notification_title(self, status):
        titles = {
            'accepted': 'Driver Accepted',
            'arrived': 'Driver Has Arrived', 
            'ongoing': 'Trip Started',
            'completed': 'Trip Completed',
            'cancelled': 'Trip Cancelled'
        }
        return titles.get(status, 'Status Update')


class DriverLocationConsumer(AsyncWebsocketConsumer):
    """Handle driver location broadcasting to nearby students"""
    
    async def connect(self):
        self.driver_id = self.scope['url_route']['kwargs']['driver_id']
        self.driver_group_name = f'driver_{self.driver_id}'
        
        user = self.scope['user']
        if not user.is_authenticated or (user.role != 'driver' and user.id != self.driver_id):
            await self.close()
        else:
            await self.channel_layer.group_add(
                self.driver_group_name,
                self.channel_name
            )
            await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.driver_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        if data.get('type') == 'location':
            # Update driver's current location
            await self.update_driver_location(
                self.driver_id,
                data['latitude'],
                data['longitude']
            )
            
            # This would broadcast to students looking for nearby drivers
            # You can implement a geospatial broadcast system here
    
    @database_sync_to_async
    def update_driver_location(self, driver_id, lat, lng):
        profile = DriverProfile.objects.get(user_id=driver_id)
        profile.current_latitude = lat
        profile.current_longitude = lng
        profile.last_location_update = timezone.now()
        profile.save()