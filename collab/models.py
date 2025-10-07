from django.db import models


class CollabRoom(models.Model):
    """
    Stores the state of collaborative editing rooms.
    Supports both Simple Sync (text) and Y.js CRDT (binary state).
    """
    room_name = models.CharField(
        max_length=100, 
        unique=True,
        db_index=True,
        help_text="Unique identifier for the collaboration room"
    )
    
    # For Y.js CRDT - stores the binary state vector
    yjs_state = models.BinaryField(
        null=True, 
        blank=True,
        help_text="Y.js binary state (state vector)"
    )
    
    # For Simple Sync - stores plain text content
    text_content = models.TextField(
        blank=True,
        default="",
        help_text="Plain text content for simple sync rooms"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Collaboration Room"
        verbose_name_plural = "Collaboration Rooms"
    
    def __str__(self):
        return f"Room: {self.room_name}"
