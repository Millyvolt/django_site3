from django.contrib import admin
from .models import CollabRoom


@admin.register(CollabRoom)
class CollabRoomAdmin(admin.ModelAdmin):
    """Admin interface for collaboration rooms."""
    list_display = ['room_name', 'updated_at', 'created_at', 'has_yjs_state', 'text_preview']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['room_name', 'text_content']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_yjs_state(self, obj):
        """Check if room has Y.js state."""
        return bool(obj.yjs_state)
    has_yjs_state.boolean = True
    has_yjs_state.short_description = 'Has Y.js State'
    
    def text_preview(self, obj):
        """Show preview of text content."""
        if obj.text_content:
            return obj.text_content[:50] + ('...' if len(obj.text_content) > 50 else '')
        return '-'
    text_preview.short_description = 'Text Preview'
