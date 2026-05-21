from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification

def create_notification(user_id, notification_type, title, message, related_trip_id=None):
    """Create a notification and send it via WebSocket"""
    # Save to database
    notification = Notification.objects.create(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        related_trip_id=related_trip_id
    )
    
    # Send via WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'notifications_{user_id}',
        {
            'type': 'send_notification',
            'id': notification.id,
            'title': title,
            'message': message,
            'notification_type': notification_type,
            'created_at': notification.created_at.isoformat(),
            'related_trip_id': related_trip_id,
        }
    )
    
    return notification

def notify_driver_new_request(driver_id, trip_id, pickup_location):
    """Notify driver of a new ride request"""
    create_notification(
        user_id=driver_id,
        notification_type='ride_request',
        title='New Ride Request',
        message=f'New ride request from {pickup_location}',
        related_trip_id=trip_id
    )

def notify_student_driver_accepted(student_id, driver_name, trip_id):
    """Notify student that driver accepted the ride"""
    create_notification(
        user_id=student_id,
        notification_type='ride_accepted',
        title='Driver Accepted',
        message=f'{driver_name} has accepted your ride request',
        related_trip_id=trip_id
    )

def notify_student_driver_arrived(student_id, driver_name, trip_id):
    """Notify student that driver has arrived"""
    create_notification(
        user_id=student_id,
        notification_type='driver_arrived',
        title='Driver Has Arrived',
        message=f'{driver_name} has arrived at your pickup location',
        related_trip_id=trip_id
    )

def notify_ride_cancelled(user_id, cancelled_by, trip_id):
    """Notify user that ride was cancelled"""
    create_notification(
        user_id=user_id,
        notification_type='ride_cancelled',
        title='Ride Cancelled',
        message=f'Your ride has been cancelled by {cancelled_by}',
        related_trip_id=trip_id
    )

def notify_ride_completed(user_id, trip_id, fare):
    """Notify user that ride is completed"""
    create_notification(
        user_id=user_id,
        notification_type='ride_completed',
        title='Ride Completed',
        message=f'Your ride is complete. Fare: ₦{fare}',
        related_trip_id=trip_id
    )