"""
WebSocket consumer for collaborative editing.
Handles real-time message broadcasting between users in the same room.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer


class CollaborationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer that relays messages between clients.
    
    Each client connects to a room identified by room_name.
    Messages are broadcast to all clients in the same room.
    """
    
    async def connect(self):
        """Handle new WebSocket connection."""
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
        Receive message from WebSocket and broadcast to room.
        
        Supports both text (Simple Sync) and binary (Y.js) messages.
        """
        if text_data:
            # Text message - broadcast to all room members
            print(f"Received text in room {self.room_name}, preview: {text_data[:50]}...")
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'collaboration_message',
                    'text_data': text_data
                }
            )
        elif bytes_data:
            # Binary Y.js update - broadcast to all room members
            print(f"Received Y.js binary update in room {self.room_name}, size: {len(bytes_data)} bytes")
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'collaboration_message',
                    'bytes_data': bytes_data
                }
            )
    
    async def collaboration_message(self, event):
        """
        Receive message from room group and send to WebSocket.
        """
        if 'text_data' in event:
            # Send text message
            await self.send(text_data=event['text_data'])
        elif 'bytes_data' in event:
            # Send binary Y.js update
            await self.send(bytes_data=event['bytes_data'])

