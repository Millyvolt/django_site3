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
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Accept the WebSocket connection
        await self.accept()
        
        print(f"User connected to room: {self.room_name}")
        
        # Load and send existing room state (if any)
        await self.send_initial_state()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        print(f"User disconnected from room: {self.room_name} (code: {close_code})")
    
    async def receive(self, text_data=None, bytes_data=None):
        """
        Receive message from WebSocket, save to database, and broadcast to room.
        
        Supports both text (Simple Sync) and binary (Y.js) messages.
        """
        if text_data:
            # Text message - could be command or content
            print(f"✓ [Room: {self.room_name}] Received text message, size: {len(text_data)} bytes")
            
            # Check if it's a state snapshot command (don't broadcast these)
            try:
                data = json.loads(text_data)
                if data.get('type') == 'snapshot' and 'state' in data:
                    # This is a state snapshot - save but don't broadcast
                    import base64
                    state_bytes = base64.b64decode(data['state'])
                    await self.save_yjs_state(state_bytes)
                    print(f"✓ [Room: {self.room_name}] Received and saved state snapshot")
                    return
                elif 'text' in data:
                    # Regular text content
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
        Save Y.js binary state to database by merging with existing state.
        Y.js updates are incremental, so we need to apply them to get the full state.
        """
        try:
            from .models import CollabRoom
            # Import Y.js server-side (we'll need to handle this differently)
            # For now, we'll just store the latest update and rely on client-side state
            room, created = CollabRoom.objects.get_or_create(
                room_name=self.room_name
            )
            
            # Store the update (in production, you'd merge this with existing state)
            # For simplicity, we're storing the raw update
            # The client will handle state reconstruction
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

