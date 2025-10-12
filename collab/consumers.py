"""
WebSocket consumer for collaborative editing.
Handles real-time message broadcasting between users in the same room.
Includes persistence layer for storing and loading room states.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class CollaborationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer that relays messages between clients.
    
    Each client connects to a room identified by room_name.
    Messages are broadcast to all clients in the same room.
    """
    
    async def connect(self):
        """Handle new WebSocket connection and send initial room state."""
        # Get room name from URL route
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'collab_{self.room_name}'
        
        # Get user information from scope
        user = self.scope.get('user')
        if user and user.is_authenticated:
            self.user_id = user.id
            self.username = user.username
            # Get user avatar URL if available
            try:
                from polls.models import UserProfile
                profile = await self.get_user_profile(user.id)
                self.user_avatar = profile['avatar_url'] if profile else None
            except:
                self.user_avatar = None
        else:
            self.user_id = None
            self.username = 'Anonymous'
            self.user_avatar = None
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Accept the WebSocket connection
        await self.accept()
        
        print(f"User {self.username} (ID: {self.user_id}) connected to room: {self.room_name}")
        
        # Load and send existing room state (if any)
        await self.send_initial_state()
        
        # Broadcast user join event to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user_id,
                'username': self.username,
                'avatar': self.user_avatar,
                'sender_channel': self.channel_name
            }
        )
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Broadcast user leave event to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': self.user_id,
                'username': self.username,
                'sender_channel': self.channel_name
            }
        )
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        print(f"User {self.username} disconnected from room: {self.room_name} (code: {close_code})")
    
    async def receive(self, text_data=None, bytes_data=None):
        """
        Receive message from WebSocket, save to database, and broadcast to room.
        
        Supports both text (Simple Sync) and binary (Y.js) messages, plus awareness updates.
        """
        if text_data:
            # Text message - could be command, content, or awareness
            print(f"✓ [Room: {self.room_name}] Received text message, size: {len(text_data)} bytes")
            
            # Check if it's a special message type
            try:
                data = json.loads(text_data)
                
                # Awareness update (cursor/selection position)
                if data.get('type') == 'awareness':
                    print(f"✓ [Room: {self.room_name}] Awareness update from {self.username}")
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'awareness_update',
                            'user_id': self.user_id,
                            'username': self.username,
                            'avatar': self.user_avatar,
                            'awareness_data': data.get('data'),
                            'sender_channel': self.channel_name
                        }
                    )
                    return
                
                # State sync request from new client
                elif data.get('type') == 'request_state':
                    print(f"✓ [Room: {self.room_name}] State sync request from {self.username}")
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'state_request',
                            'requester_channel': self.channel_name
                        }
                    )
                    return
                
                # Full state response from existing client
                elif data.get('type') == 'full_state' and 'state_vector' in data:
                    print(f"✓ [Room: {self.room_name}] Received full state from {self.username}")
                    # Broadcast to the requester
                    target_channel = data.get('target_channel')
                    if target_channel:
                        await self.channel_layer.send(
                            target_channel,
                            {
                                'type': 'state_sync',
                                'state_vector': data['state_vector']
                            }
                        )
                    return
                
                # State snapshot - save but don't broadcast
                elif data.get('type') == 'snapshot' and 'state' in data:
                    import base64
                    state_bytes = base64.b64decode(data['state'])
                    await self.save_yjs_state(state_bytes)
                    print(f"✓ [Room: {self.room_name}] Received and saved state snapshot")
                    return
                
                # Regular text content
                elif 'text' in data:
                    await self.save_text_content(data['text'])
            except json.JSONDecodeError:
                print(f"⚠️  [Room: {self.room_name}] Could not parse text data as JSON")
            
            print(f"✓ [Room: {self.room_name}] Broadcasting text message to room")
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'collaboration_message',
                    'text_data': text_data,
                    'sender_channel': self.channel_name
                }
            )
        elif bytes_data:
            # Binary Y.js update - broadcast to all room members (including sender for echo)
            print(f"✓ [Room: {self.room_name}] Received Y.js binary update, size: {len(bytes_data)} bytes")
            print(f"   First bytes (hex): {bytes_data[:min(20, len(bytes_data))].hex()}")
            
            # Save Y.js state for persistence
            await self.save_yjs_state(bytes_data)
            
            print(f"✓ [Room: {self.room_name}] Broadcasting binary message to room")
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'collaboration_message',
                    'bytes_data': bytes_data,
                    'sender_channel': self.channel_name
                }
            )
        else:
            print(f"⚠️  [Room: {self.room_name}] Received empty message (no text_data or bytes_data)")
    
    async def collaboration_message(self, event):
        """
        Receive message from room group and send to WebSocket.
        Excludes the sender to avoid echo (Y.js handles its own updates locally).
        """
        # Don't echo back to sender - Y.js applies changes locally
        if event.get('sender_channel') == self.channel_name:
            print(f"✓ [Room: {self.room_name}] Skipping echo to sender")
            return
        
        if 'text_data' in event:
            # Send text message
            await self.send(text_data=event['text_data'])
        elif 'bytes_data' in event:
            # Send binary Y.js update
            print(f"✓ [Room: {self.room_name}] Forwarding binary update to other client ({len(event['bytes_data'])} bytes)")
            await self.send(bytes_data=event['bytes_data'])
    
    async def user_joined(self, event):
        """Notify client that a user joined the room."""
        # Don't send to the user who just joined
        if event.get('sender_channel') == self.channel_name:
            return
        
        message = json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username'],
            'avatar': event['avatar']
        })
        await self.send(text_data=message)
        print(f"✓ [Room: {self.room_name}] Notified client about user join: {event['username']}")
    
    async def user_left(self, event):
        """Notify client that a user left the room."""
        # Don't send to the user who just left
        if event.get('sender_channel') == self.channel_name:
            return
        
        message = json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username']
        })
        await self.send(text_data=message)
        print(f"✓ [Room: {self.room_name}] Notified client about user leave: {event['username']}")
    
    async def awareness_update(self, event):
        """Forward awareness update to other clients."""
        # Don't echo back to sender
        if event.get('sender_channel') == self.channel_name:
            return
        
        message = json.dumps({
            'type': 'awareness_update',
            'user_id': event['user_id'],
            'username': event['username'],
            'avatar': event['avatar'],
            'data': event['awareness_data']
        })
        await self.send(text_data=message)
        # Debug logging removed to reduce noise
    
    async def state_request(self, event):
        """Handle state sync request from new client."""
        # Don't send to requester
        if event.get('requester_channel') == self.channel_name:
            return
        
        message = json.dumps({
            'type': 'state_request',
            'requester_channel': event['requester_channel']
        })
        await self.send(text_data=message)
        print(f"✓ [Room: {self.room_name}] Forwarded state request to {self.username}")
    
    async def state_sync(self, event):
        """Send full state to requesting client."""
        message = json.dumps({
            'type': 'state_sync',
            'state_vector': event['state_vector']
        })
        await self.send(text_data=message)
        print(f"✓ [Room: {self.room_name}] Sent state sync to client")
    
    # Database operations (async wrappers)
    
    @database_sync_to_async
    def get_or_create_room(self):
        """Get or create a room in the database."""
        from .models import CollabRoom
        room, created = CollabRoom.objects.get_or_create(
            room_name=self.room_name
        )
        return room, created
    
    @database_sync_to_async
    def save_yjs_state(self, update_bytes):
        """
        Save Y.js binary state to database.
        Stores the latest update - new clients will request full state from connected peers.
        """
        try:
            from .models import CollabRoom
            room, created = CollabRoom.objects.get_or_create(
                room_name=self.room_name
            )
            
            # Store the latest update
            room.yjs_state = bytes(update_bytes)
            room.save(update_fields=['yjs_state', 'updated_at'])
            print(f"✓ Saved Y.js update for room {self.room_name} ({len(update_bytes)} bytes)")
        except Exception as e:
            print(f"✗ Error saving Y.js state: {e}")
    
    @database_sync_to_async
    def save_text_content(self, text):
        """Save plain text content to database."""
        from .models import CollabRoom
        room, created = CollabRoom.objects.get_or_create(
            room_name=self.room_name
        )
        room.text_content = text
        room.save(update_fields=['text_content', 'updated_at'])
        print(f"✓ Saved text content for room {self.room_name} ({len(text)} chars)")
    
    @database_sync_to_async
    def get_room_state(self):
        """Retrieve existing room state from database."""
        from .models import CollabRoom
        try:
            room = CollabRoom.objects.get(room_name=self.room_name)
            return {
                'yjs_state': room.yjs_state,
                'text_content': room.text_content
            }
        except CollabRoom.DoesNotExist:
            return {'yjs_state': None, 'text_content': ''}
    
    async def send_initial_state(self):
        """Send existing room state to newly connected client."""
        state = await self.get_room_state()
        
        # Send Y.js state if available
        if state['yjs_state']:
            print(f"Sending initial Y.js state to new client: {len(state['yjs_state'])} bytes")
            await self.send(bytes_data=state['yjs_state'])
        
        # Send text content if available (for Simple Sync rooms)
        if state['text_content']:
            print(f"Sending initial text content to new client: {len(state['text_content'])} chars")
            text_message = json.dumps({'text': state['text_content']})
            await self.send(text_data=text_message)
    
    @database_sync_to_async
    def get_user_profile(self, user_id):
        """Get user profile information including avatar URL."""
        from polls.models import UserProfile
        try:
            profile = UserProfile.objects.get(user_id=user_id)
            return {
                'avatar_url': profile.get_profile_image_url
            }
        except UserProfile.DoesNotExist:
            return None

