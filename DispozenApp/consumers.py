import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models import Q
from .models import Notification


class NotificationConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        
        user = self.scope.get('user')
        
        if not user or user.is_anonymous:
            print("❌ Unauthenticated WebSocket connection attempt.")
            await self.close()
            return
        
        print(f"✅ WebSocket connection established for user: {user.id} ({user.email})")
        
        self.user = user
        self.group_name = f"user_{user.id}"
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        
        try:
            notifications = await self.get_unread_notifications()
            unread_count = await self.get_unread_count()
            
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to notification service',
                'unread_count': unread_count,
                'notifications': notifications  
            }))
        except Exception as e:
            print(f"❌ Error fetching notifications: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to notification service',
                'unread_count': 0,
                'notifications': []
            }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'group_name'):
            print(f"🔌 WebSocket disconnected for group: {self.group_name} (code: {close_code})")
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle messages received from the WebSocket client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'message': 'Connection alive'
                }))
            
            elif message_type == 'mark_as_read':
                notification_id = data.get('notification_id')
                if notification_id:
                    success = await self.mark_notification_as_read(notification_id)
                    unread_count = await self.get_unread_count()
                    await self.send(text_data=json.dumps({
                        'type': 'notification_marked',
                        'notification_id': notification_id,
                        'success': success,
                        'unread_count': unread_count
                    }))
            
            elif message_type == 'mark_all_as_read':
                count = await self.mark_all_as_read()
                await self.send(text_data=json.dumps({
                    'type': 'all_notifications_marked',
                    'count': count,
                    'unread_count': 0
                }))
            
            elif message_type == 'get_notifications':
                
                limit = data.get('limit', 10)
                notifications = await self.get_unread_notifications(limit)
                unread_count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'notifications_list',
                    'notifications': notifications,
                    'unread_count': unread_count
                }))
            
            elif message_type == 'get_all_notifications':
                
                limit = data.get('limit', 10)
                notifications = await self.get_all_notifications(limit)
                await self.send(text_data=json.dumps({
                    'type': 'all_notifications_list',
                    'notifications': notifications
                }))
            
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            print(f"❌ Error in receive: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))

    async def send_notification(self, event):
        """Send notification to WebSocket client (called by channel_layer.group_send)."""
        message = event.get('message', {})
        
       
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': {
                'content': message.get('content')
            }
        }))
        
        print(f"📧 Notification sent: {message.get('content', 'N/A')}")

    
    
    @database_sync_to_async
    def get_unread_notifications(self, limit=10):
        """
        Fetch unread notifications - returns only content.
        FIXED: Now checks BOTH partner and organizer fields.
        """
        try:
            
            notifications = Notification.objects.filter(
                Q(partner=self.user, is_read=False) | Q(organizer=self.user, is_read=False)
            ).order_by('-created_at')[:limit]
            
            return [{'content': n.content} for n in notifications]
        except Exception as e:
            print(f"❌ Error fetching notifications: {str(e)}")
            return []

    @database_sync_to_async
    def get_all_notifications(self, limit=10):
        """
        Fetch all notifications (read + unread) - returns only content.
        FIXED: Now checks BOTH partner and organizer fields.
        """
        try:
            
            notifications = Notification.objects.filter(
                Q(partner=self.user) | Q(organizer=self.user)
            ).order_by('-created_at')[:limit]
            
            return [{'content': n.content} for n in notifications]
        except Exception as e:
            print(f"❌ Error fetching notifications: {str(e)}")
            return []

    @database_sync_to_async
    def get_unread_count(self):
        """
        Get count of unread notifications.
        FIXED: Now checks BOTH partner and organizer fields.
        """
        try:
            
            return Notification.objects.filter(
                Q(partner=self.user, is_read=False) | Q(organizer=self.user, is_read=False)
            ).count()
        except Exception as e:
            print(f"❌ Error counting notifications: {str(e)}")
            return 0

    @database_sync_to_async
    def mark_notification_as_read(self, notification_id):
        """
        Mark a notification as read.
        FIXED: Now checks BOTH partner and organizer fields.
        """
        try:
            
            notification = Notification.objects.get(
                Q(id=notification_id) & (Q(partner=self.user) | Q(organizer=self.user))
            )
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            print(f"✅ Notification {notification_id} marked as read")
            return True
        except Notification.DoesNotExist:
            print(f"❌ Notification {notification_id} not found or access denied")
            return False
        except Exception as e:
            print(f"❌ Error marking notification as read: {str(e)}")
            return False

    @database_sync_to_async
    def mark_all_as_read(self):
        """
        Mark all notifications as read.
        FIXED: Now checks BOTH partner and organizer fields.
        """
        try:
            
            count = Notification.objects.filter(
                Q(partner=self.user, is_read=False) | Q(organizer=self.user, is_read=False)
            ).update(is_read=True)
            print(f"✅ Marked {count} notifications as read")
            return count
        except Exception as e:
            print(f"❌ Error marking all as read: {str(e)}")
            return 0

