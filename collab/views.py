from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def collab_home(request):
    """
    Home page for collaborative editor.
    Lists available rooms or allows creating a new room.
    """
    return render(request, 'collab/home.html')


def collab_room(request, room_name):
    """
    Collaborative editor room.
    Users can join a room by name and collaborate in real-time.
    """
    return render(request, 'collab/room_simple.html', {
        'room_name': room_name,
        'username': request.user.username if request.user.is_authenticated else 'Anonymous'
    })
