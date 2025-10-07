"""
URL configuration for the collab app.
"""

from django.urls import path
from . import views

app_name = 'collab'

urlpatterns = [
    path('', views.collab_home, name='home'),
    path('<str:room_name>/', views.collab_room, name='room'),
]

