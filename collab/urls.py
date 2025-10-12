"""
URL configuration for the collab app.
"""

from django.urls import path
from . import views

app_name = 'collab'

urlpatterns = [
    path('', views.collab_home, name='home'),
    path('yjs/<str:room_name>/', views.collab_room_yjs, name='room_yjs'),
    path('monaco/<str:room_name>/', views.collab_room_monaco, name='room_monaco'),
    path('monaco-yjs/<str:room_name>/', views.collab_room_monaco_yjs, name='room_monaco_yjs'),
    path('<str:room_name>/', views.collab_room, name='room'),
]

