"""
WebSocket URL routing for the collab app.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/collab/(?P<room_name>\w+)/$', consumers.CollaborationConsumer.as_asgi()),
]

