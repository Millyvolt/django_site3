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
    Collaborative editor room (Simple Sync).
    Users can join a room by name and collaborate in real-time.
    """
    return render(request, 'collab/room_simple.html', {
        'room_name': room_name,
        'username': request.user.username if request.user.is_authenticated else 'Anonymous',
        'user': request.user
    })


def collab_room_yjs(request, room_name):
    """
    Collaborative editor room with Y.js CRDT support.
    Uses Y.js for conflict-free replicated data type synchronization.
    """
    return render(request, 'collab/room_yjs.html', {
        'room_name': room_name,
        'username': request.user.username if request.user.is_authenticated else 'Anonymous',
        'user': request.user
    })


def collab_room_monaco(request, room_name):
    """
    Collaborative editor room with Monaco Editor (IDE).
    Full-featured IDE experience with IntelliSense and advanced features.
    Supports multiple programming languages.
    """
    # Get language from query parameter, default to C++
    language = request.GET.get('lang', 'cpp')
    
    return render(request, 'collab/room_monaco.html', {
        'room_name': room_name,
        'username': request.user.username if request.user.is_authenticated else 'Anonymous',
        'user': request.user,
        'language': language
    })


def collab_room_monaco_yjs(request, room_name):
    """
    Collaborative editor room with Monaco Editor + Y.js CRDT.
    Provides conflict-free collaborative editing with Y.js operational transformation.
    Perfect synchronization across multiple users without conflicts.
    """
    # Get language from query parameter, default to C++
    language = request.GET.get('lang', 'cpp')
    
    return render(request, 'collab/room_monaco_yjs.html', {
        'room_name': room_name,
        'username': request.user.username if request.user.is_authenticated else 'Anonymous',
        'user': request.user,
        'language': language
    })
