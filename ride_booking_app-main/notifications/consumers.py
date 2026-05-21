import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Notification

class NotificationConsumer(AsyncWebsocketConsumer):
    """Real-time notifications for users"""
    
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f'notifications_{self.user_id}'
        
        user = self.scope['user']
        if not user.is_authenticated or user.id != self.user_id:
            await self.close()
        else:
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            
            # Send unread count on connect
            await self.send_unread_count()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle client messages (e.g., mark as read)"""
        data = json.loads(text_data)
        
        if data.get('type') == 'mark_read':
            await self.mark_notifications_read(data.get('notification_ids', []))
            await self.send_unread_count()
    
    async def send_notification(self, event):
        """Send notification to client"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'id': event['id'],
            'title': event['title'],
            'message': event['message'],
            'notification_type': event['notification_type'],
            'created_at': event['created_at'],
            'related_trip_id': event.get('related_trip_id'),
        }))
    
    async def send_unread_count(self):
        """Send unread notification count"""
        count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': count
        }))
    
    @database_sync_to_async
    def get_unread_count(self):
        return Notification.objects.filter(
            user_id=self.user_id,
            is_read=False
        ).count()
    
    @database_sync_to_async
    def mark_notifications_read(self, notification_ids):
        Notification.objects.filter(
            id__in=notification_ids,
            user_id=self.user_id
        ).update(is_read=True)