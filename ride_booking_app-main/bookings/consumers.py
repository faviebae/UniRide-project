# bookings/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

# DO NOT import models at the top level - import inside methods instead

class TripTrackingConsumer(AsyncWebsocketConsumer):
    """Handle real-time trip tracking for students"""
    
    async def connect(self):
        self.trip_id = self.scope['url_route']['kwargs']['trip_id']
        self.trip_group_name = f'trip_{self.trip_id}'
        
        # Check if user is authorized (student or driver of this trip)
        user = self.scope['user']
        
        if not user.is_authenticated:
            await self.close()
            return
        
        # Import model inside the method
        from .models import Trip
        
        try:
            trip = await self.get_trip(self.trip_id)
            if not trip:
                await self.close()
                return
                
            if user.role == 'student' and trip.student_id != user.id:
                await self.close()
                return
            elif user.role == 'driver' and trip.driver_id != user.id:
                await self.close()
                return
        except Exception as e:
            print(f"Error in connect: {e}")
            await self.close()
            return
        
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
    
    @database_sync_to_async
    def get_trip(self, trip_id):
        from .models import Trip
        try:
            return Trip.objects.get(id=trip_id)
        except Trip.DoesNotExist:
            return None
    
    @database_sync_to_async
    def save_trip_location(self, trip_id, lat, lng):
        from .models import TripLocation
        TripLocation.objects.create(
            trip_id=trip_id,
            latitude=lat,
            longitude=lng
        )
    
    @database_sync_to_async
    def update_trip_status(self, trip_id, status):
        from .models import Trip
        trip = Trip.objects.get(id=trip_id)
        trip.status = status
        if status == 'accepted':
            trip.accepted_at = timezone.now()
        elif status == 'ongoing':
            trip.started_at = timezone.now()
        elif status == 'completed':
            trip.completed_at = timezone.now()
        trip.save()


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
    
    @database_sync_to_async
    def update_driver_location(self, driver_id, lat, lng):
        from users.models import DriverProfile
        try:
            profile = DriverProfile.objects.get(user_id=driver_id)
            profile.current_latitude = lat
            profile.current_longitude = lng
            profile.last_location_update = timezone.now()
            profile.save()
        except DriverProfile.DoesNotExist:
            pass



class RideUpdateConsumer(AsyncWebsocketConsumer):
    """Real-time dashboard updates for both students and drivers"""
    
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Create a unique group for this user
        self.group_name = f'user_{self.user.id}'
        
        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        
        # Send initial data immediately
        await self.send_initial_data()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages from client (like refresh requests)"""
        try:
            data = json.loads(text_data)
            if data.get('type') == 'refresh':
                await self.send_initial_data()
        except:
            pass
    
    async def send_initial_data(self):
        """Send current dashboard data to the connected user"""
        if self.user.role == 'student':
            data = await self.get_student_data()
        elif self.user.role == 'driver':
            data = await self.get_driver_data()
        else:
            data = {}
        
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'data': data
        }))
    
    async def dashboard_update(self, event):
        """Send dashboard update to user"""
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_student_data(self):
        from django.db.models import Sum
        from .models import Trip
        
        # Get active trip
        active_trip = Trip.objects.filter(
            student=self.user,
            status__in=['searching', 'accepted', 'arrived', 'ongoing']
        ).first()
        
        # Get completed trips stats
        completed_trips = Trip.objects.filter(
            student=self.user,
            status='completed'
        )
        
        total_trips = completed_trips.count()
        total_spent = completed_trips.aggregate(Sum('total_fare'))['total_fare__sum'] or 0
        
        active_trip_data = None
        if active_trip:
            active_trip_data = {
                'id': active_trip.id,
                'status': active_trip.status,
                'pickup_address': active_trip.pickup_address,
                'dropoff_address': active_trip.dropoff_address,
                'total_fare': str(active_trip.total_fare),
            }
            if active_trip.driver:
                active_trip_data['driver_name'] = active_trip.driver.get_full_name()
                active_trip_data['driver_phone'] = str(active_trip.driver.phone_number)
        
        return {
            'total_trips': total_trips,
            'total_spent': float(total_spent),
            'wallet_balance': float(self.user.wallet_balance),
            'active_trip': active_trip_data,
            'role': 'student',
        }
    
    @database_sync_to_async
    def get_driver_data(self):
        from django.db.models import Sum
        from .models import Trip
        
        # Get active trip
        active_trip = Trip.objects.filter(
            driver=self.user,
            status__in=['accepted', 'arrived', 'ongoing']
        ).first()
        
        # Get available ride requests (unassigned, searching)
        available_rides = Trip.objects.filter(
            status='searching',
            driver__isnull=True
        ).select_related('student').order_by('-requested_at')[:10]
        
        # Get completed trips stats
        completed_trips = Trip.objects.filter(
            driver=self.user,
            status='completed'
        )
        
        total_earnings = completed_trips.aggregate(Sum('total_fare'))['total_fare__sum'] or 0
        completed_count = completed_trips.count()
        
        active_trip_data = None
        if active_trip:
            active_trip_data = {
                'id': active_trip.id,
                'status': active_trip.status,
                'pickup_address': active_trip.pickup_address,
                'dropoff_address': active_trip.dropoff_address,
                'total_fare': str(active_trip.total_fare),
                'student_name': active_trip.student.get_full_name(),
                'student_phone': str(active_trip.student.phone_number),
            }
        
        available_rides_data = []
        for ride in available_rides:
            available_rides_data.append({
                'id': ride.id,
                'pickup_address': ride.pickup_address,
                'dropoff_address': ride.dropoff_address,
                'total_fare': str(ride.total_fare),
                'student_name': ride.student.get_full_name(),
                'requested_at': ride.requested_at.isoformat(),
            })
        
        return {
            'active_trip': active_trip_data,
            'available_rides': available_rides_data,
            'total_earnings': float(total_earnings),
            'completed_trips': completed_count,
            'is_available': self.user.is_available,
            'role': 'driver',
        }