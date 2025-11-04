import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models import Q
from .models import Notification


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time notifications.
    Returns only content field for notifications.
    Works for both partners and organizers.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
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
        
        # Fetch unread notifications and send to client
        try:
            notifications = await self.get_unread_notifications()
            unread_count = await self.get_unread_count()
            
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to notification service',
                'unread_count': unread_count,
                'notifications': notifications  # Only contains content field
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
                # Get unread notifications only
                limit = data.get('limit', 10)
                notifications = await self.get_unread_notifications(limit)
                unread_count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'notifications_list',
                    'notifications': notifications,
                    'unread_count': unread_count
                }))
            
            elif message_type == 'get_all_notifications':
                # Get ALL notifications (read + unread)
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
        
        # Send only content field
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': {
                'content': message.get('content')
            }
        }))
        
        print(f"📧 Notification sent: {message.get('content', 'N/A')}")

    # ===== DATABASE HELPER METHODS =====
    
    @database_sync_to_async
    def get_unread_notifications(self, limit=10):
        """
        Fetch unread notifications - returns only content.
        FIXED: Now checks BOTH partner and organizer fields.
        """
        try:
            # ✅ FIX: Check if user is EITHER partner OR organizer
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
            # ✅ FIX: Check if user is EITHER partner OR organizer
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
            # ✅ FIX: Check if user is EITHER partner OR organizer
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
            # ✅ FIX: Check if user is EITHER partner OR organizer
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
            # ✅ FIX: Check if user is EITHER partner OR organizer
            count = Notification.objects.filter(
                Q(partner=self.user, is_read=False) | Q(organizer=self.user, is_read=False)
            ).update(is_read=True)
            print(f"✅ Marked {count} notifications as read")
            return count
        except Exception as e:
            print(f"❌ Error marking all as read: {str(e)}")
            return 0

# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from .models import Notification


# class NotificationConsumer(AsyncWebsocketConsumer):
#     """
#     WebSocket consumer for handling real-time notifications.
    
#     Supports:
#     - Real-time notification delivery
#     - Fetching unread notifications on connection
#     - Marking notifications as read
#     - Ping/pong for connection health
#     """
    
#     async def connect(self):
#         """
#         Handle WebSocket connection.
#         Authenticate user and add them to their personal notification group.
#         """
#         # Get the user from the scope (set by JWTAuthMiddleware)
#         user = self.scope.get('user')
        
#         # Check if user is authenticated
#         if not user or user.is_anonymous:
#             print("❌ Unauthenticated WebSocket connection attempt.")
#             await self.close()
#             return
        
#         print(f"✅ WebSocket connection established for user: {user.id} ({user.email})")
        
#         # Store user for later use
#         self.user = user
        
#         # Create a unique group name for this user
#         self.group_name = f"user_{user.id}"
        
#         # Add this WebSocket connection to the user's notification group
#         await self.channel_layer.group_add(
#             self.group_name,
#             self.channel_name
#         )
        
#         # Accept the WebSocket connection
#         await self.accept()
        
#         # Fetch unread notifications and send to client
#         try:
#             notifications = await self.get_unread_notifications()
#             unread_count = await self.get_unread_count()
            
#             # Send welcome message with unread notifications
#             await self.send(text_data=json.dumps({
#                 'type': 'connection_established',
#                 'message': 'Connected to notification service',
#                 'unread_count': unread_count,
#                 'notifications': notifications
#             }))
#         except Exception as e:
#             print(f"❌ Error fetching notifications: {str(e)}")
#             # Still send connection confirmation even if fetching fails
#             await self.send(text_data=json.dumps({
#                 'type': 'connection_established',
#                 'message': 'Connected to notification service',
#                 'unread_count': 0,
#                 'notifications': []
#             }))

#     async def disconnect(self, close_code):
#         """
#         Handle WebSocket disconnection.
#         Remove the user from their notification group.
#         """
#         # Only try to remove from group if group_name was set
#         if hasattr(self, 'group_name'):
#             print(f"🔌 WebSocket disconnected for group: {self.group_name} (code: {close_code})")
#             await self.channel_layer.group_discard(
#                 self.group_name,
#                 self.channel_name
#             )

#     async def receive(self, text_data):
#         """
#         Handle messages received from the WebSocket client.
#         """
#         try:
#             data = json.loads(text_data)
#             message_type = data.get('type')
            
#             # Handle different message types
#             if message_type == 'ping':
#                 await self.send(text_data=json.dumps({
#                     'type': 'pong',
#                     'message': 'Connection alive'
#                 }))
            
#             elif message_type == 'mark_as_read':
#                 # Mark notification as read
#                 notification_id = data.get('notification_id')
#                 if notification_id:
#                     success = await self.mark_notification_as_read(notification_id)
#                     unread_count = await self.get_unread_count()
#                     await self.send(text_data=json.dumps({
#                         'type': 'notification_marked',
#                         'notification_id': notification_id,
#                         'success': success,
#                         'unread_count': unread_count
#                     }))
            
#             elif message_type == 'mark_all_as_read':
#                 # Mark all notifications as read
#                 count = await self.mark_all_as_read()
#                 await self.send(text_data=json.dumps({
#                     'type': 'all_notifications_marked',
#                     'count': count,
#                     'unread_count': 0
#                 }))
            
#             elif message_type == 'get_notifications':
#                 # Fetch and send notifications
#                 limit = data.get('limit', 10)
#                 notifications = await self.get_unread_notifications(limit)
#                 unread_count = await self.get_unread_count()
#                 await self.send(text_data=json.dumps({
#                     'type': 'notifications_list',
#                     'notifications': notifications,
#                     'unread_count': unread_count
#                 }))
            
#             else:
#                 await self.send(text_data=json.dumps({
#                     'type': 'error',
#                     'message': f'Unknown message type: {message_type}'
#                 }))
                
#         except json.JSONDecodeError:
#             await self.send(text_data=json.dumps({
#                 'type': 'error',
#                 'message': 'Invalid JSON format'
#             }))
#         except Exception as e:
#             print(f"❌ Error in receive: {str(e)}")
#             await self.send(text_data=json.dumps({
#                 'type': 'error',
#                 'message': 'Internal server error'
#             }))

#     async def send_notification(self, event):
#         """
#         Send a notification message to the WebSocket client.
#         This method is called by channel_layer.group_send()
#         """
#         # Extract the message from the event
#         message = event.get('message', {})
        
#         # Send the notification to the WebSocket
#         await self.send(text_data=json.dumps({
#             'type': 'notification',
#             'data': message
#         }))
        
#         print(f"📧 Notification sent: {message.get('title', 'N/A')}")

#     # ===== DATABASE HELPER METHODS =====
    
#     @database_sync_to_async
#     def get_unread_notifications(self, limit=10):
#         """
#         Fetch unread notifications for a user from the database.
        
#         Args:
#             limit (int): Maximum number of notifications to fetch
            
#         Returns:
#             list: List of notification dictionaries
#         """
#         try:
#             notifications = Notification.objects.filter(
#                 partner=self.user,
#                 is_read=False
#             ).select_related('organizer', 'event').order_by('-created_at')[:limit]
            
#             notifications_list = []
#             for n in notifications:
#                 notifications_list.append({
                    
#                     'content': n.content,
#                     'is_read': n.is_read,
#                 })
            
#             return notifications_list
#         except Exception as e:
#             print(f"❌ Error fetching notifications: {str(e)}")
#             return []

#     @database_sync_to_async
#     def get_unread_count(self):
#         """
#         Get count of unread notifications.
        
#         Returns:
#             int: Number of unread notifications
#         """
#         try:
#             return Notification.objects.filter(
#                 partner=self.user,
#                 is_read=False
#             ).count()
#         except Exception as e:
#             print(f"❌ Error counting notifications: {str(e)}")
#             return 0

#     @database_sync_to_async
#     def mark_notification_as_read(self, notification_id):
#         """
#         Mark a notification as read.
        
#         Args:
#             notification_id: The ID of the notification
            
#         Returns:
#             bool: True if successful, False otherwise
#         """
#         try:
#             notification = Notification.objects.get(
#                 id=notification_id,
#                 partner=self.user
#             )
#             notification.is_read = True
#             notification.save(update_fields=['is_read'])
#             print(f"✅ Notification {notification_id} marked as read")
#             return True
#         except Notification.DoesNotExist:
#             print(f"❌ Notification {notification_id} not found")
#             return False
#         except Exception as e:
#             print(f"❌ Error marking notification as read: {str(e)}")
#             return False

#     @database_sync_to_async
#     def mark_all_as_read(self):
#         """
#         Mark all notifications as read for the current user.
        
#         Returns:
#             int: Number of notifications marked as read
#         """
#         try:
#             count = Notification.objects.filter(
#                 partner=self.user,
#                 is_read=False
#             ).update(is_read=True)
#             print(f"✅ Marked {count} notifications as read")
#             return count
#         except Exception as e:
#             print(f"❌ Error marking all as read: {str(e)}")
#             return 0


# # import json
# # from channels.generic.websocket import AsyncWebsocketConsumer
# # from .models import Notification

# # class NotificationConsumer(AsyncWebsocketConsumer):
# #     """
# #     WebSocket consumer for handling real-time notifications.
    
# #     Each authenticated user connects to their own notification channel.
# #     """
    
# #     async def connect(self):
# #         """
# #         Handle WebSocket connection.
# #         Authenticate user and add them to their personal notification group.
# #         """
# #         # Get the user from the scope (set by JWTAuthMiddleware)
# #         user = self.scope.get('user')
        
# #         # Check if user is authenticated
# #         if not user or user.is_anonymous:
# #             print("❌ Unauthenticated WebSocket connection attempt.")
# #             await self.close()
# #             return
        
# #         print(f"✅ WebSocket connection established for user: {user.id} ({user.email})")
        
# #         # Create a unique group name for this user
# #         self.group_name = f"user_{user.id}"
        
# #         # Add this WebSocket connection to the user's notification group
# #         await self.channel_layer.group_add(
# #             self.group_name,
# #             self.channel_name
# #         )
        
# #         # Accept the WebSocket connection
# #         await self.accept()
        
# #         # Optionally send a welcome message
# #         # Optionally send a welcome message with recent notifications
# #         notifications = await self.get_unread_notifications(user)

# #         await self.send(text_data=json.dumps({
# #             'type': 'connection_established',
# #             'message': 'You are now connected to the notification service.',
# #             'notifications': notifications
# #         }))

# #     async def disconnect(self, close_code):
# #         """
# #         Handle WebSocket disconnection.
# #         Remove the user from their notification group.
# #         """
# #         # Only try to remove from group if group_name was set
# #         if hasattr(self, 'group_name'):
# #             print(f"🔌 WebSocket disconnected for group: {self.group_name}")
# #             await self.channel_layer.group_discard(
# #                 self.group_name,
# #                 self.channel_name
# #             )

# #     async def receive(self, text_data):
# #         """
# #         Handle messages received from the WebSocket client.
# #         Currently not implemented as this is a notification-only channel.
# #         """
# #         # You can add client-to-server message handling here if needed
# #         # For example: marking notifications as read
# #         try:
# #             data = json.loads(text_data)
# #             # Handle different message types
# #             if data.get('type') == 'ping':
# #                 await self.send(text_data=json.dumps({
# #                     'type': 'pong',
# #                     'message': 'Connection alive'
# #                 }))
# #         except json.JSONDecodeError:
# #             pass

# #     async def send_notification(self, event):
# #         """
# #         Send a notification message to the WebSocket client.
# #         This method is called by channel_layer.group_send()
# #         """
# #         # Extract the message from the event
# #         message = event.get('message', {})
        
# #         # Send the notification to the WebSocket
# #         await self.send(text_data=json.dumps({
# #             'type': 'notification',
# #             'data': message
# #         }))
        
# #         print(f"📧 Notification sent to user: {message}")



# # # import json
# # # from channels.generic.websocket import AsyncWebsocketConsumer
# # # from django.contrib.auth.models import User
# # # from .models import DispozenUser

# # # # class NotificationConsumer(AsyncWebsocketConsumer):
# # # #     async def connect(self):
# # # #         # Get the user from the WebSocket connection
# # # #         self.user = self.scope["user"]

# # # #         # Ensure the user is authenticated
# # # #         if not self.user.is_authenticated:
# # # #             await self.close()
# # # #             return

# # # #         # Create a unique room name based on the user's id
# # # #         self.room_name = f"user_{self.user.id}"
# # # #         self.room_group_name = f"notifications_{self.room_name}"

# # # #         # Join the room group
# # # #         await self.channel_layer.group_add(
# # # #             self.room_group_name,
# # # #             self.channel_name,
# # # #         )

# # # #         # Accept the WebSocket connection
# # # #         await self.accept()

# # # #     async def disconnect(self, close_code):
# # # #         # Leave the room group
# # # #         await self.channel_layer.group_discard(
# # # #             self.room_group_name,
# # # #             self.channel_name,
# # # #         )

# # # #     # Receive message from WebSocket
# # # #     async def receive(self, text_data):
# # # #         # text_data_json = json.loads(text_data)
# # # #         # message = text_data_json["message"]

# # # #         # # Send message to the WebSocket
# # # #         # await self.send(text_data=json.dumps({
# # # #         #     "message": message
# # # #         # }))
# # # #         pass

# # # #     # Send message to WebSocket when an event occurs
# # # #     async def send_notification(self, event):
# # # #         # Send message to WebSocket
# # # #         await self.send(text_data=json.dumps({
# # # #             "message": event["message"]
# # # #         }))


# # # # consumers.py
# # # # from channels.generic.websocket import AsyncWebsocketConsumer
# # # import json

# # # # class NotificationConsumer(AsyncWebsocketConsumer):
# # # #     async def connect(self):
# # # #         print("WebSocket connection established.")
# # # #         # Create a group name based on the logged-in user ID
# # # #         self.group_name = f"user_{self.scope['user'].id}"
        
# # # #         # Add the user to the group for notifications
# # # #         await self.channel_layer.group_add(
# # # #             self.group_name,  # Target group name
# # # #             self.channel_name  # WebSocket channel name
# # # #         )
# # # #         await self.accept()

# # # #     async def disconnect(self, close_code):
# # # #         # Remove the user from the group when they disconnect
# # # #         await self.channel_layer.group_discard(
# # # #             self.group_name,  # Group to remove the user from
# # # #             self.channel_name  # User's WebSocket channel
# # # #         )

# # # async def connect(self):
# # #     user = self.scope.get('user')  # CHANGED: safer way to get user
    
# # #     # NEW: Authentication check
# # #     if not user or user.is_anonymous:
# # #         print("Unauthenticated WebSocket connection attempt.")
# # #         await self.close()
# # #         return
    
# # #     print(f"WebSocket connection established for user: {user.id}")  # CHANGED: better logging
# # #     self.group_name = f"user_{user.id}"  # CHANGED: use local user variable
    
# # #     await self.channel_layer.group_add(
# # #         self.group_name,
# # #         self.channel_name
# # #     )
# # #     await self.accept()

# # # async def disconnect(self, close_code):
# # #     # NEW: Added hasattr check to prevent errors
# # #     if hasattr(self, 'group_name'):
# # #         await self.channel_layer.group_discard(
# # #             self.group_name,
# # #             self.channel_name
# # #         )

# # # async def receive(self, text_data):
# # #         # You can handle the data received from the client (optional)
# # #         # For now, it's empty as you are sending notifications only
# # #     pass

# # # async def send_notification(self, event):
# # #         # Send a notification message to the WebSocket client
# # #     await self.send(text_data=json.dumps(event))
