#!/usr/bin/env python
"""
Script to run Django with Daphne ASGI server (required for WebSocket support)
Use this instead of run_uvicorn.py when you need WebSocket/Channels functionality
"""
import os
import sys
import subprocess
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# Setup Django (required for management commands)
import django
django.setup()

from django.core.management import call_command

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Django with Daphne ASGI Server")
    print("=" * 60)
    
    # Automatic database setup for production
    print("\nSetting up database...")
    try:
        # Run migrations to ensure all tables exist
        print("Running migrations...")
        call_command('migrate', verbosity=1, interactive=False)
        
        # Create cache table if it doesn't exist
        print("Setting up cache table...")
        call_command('createcachetable', verbosity=1)
        
        print("✓ Database setup complete")
    except Exception as e:
        print(f"⚠ Warning: Database setup encountered an issue: {e}")
        print("Continuing anyway - server will start, but some features may not work.")
        print("If you see errors, run manually: python manage.py migrate && python manage.py createcachetable")
    
    print("\nServer will be available at:")
    print("  - http://localhost:8000")
    print("  - http://127.0.0.1:8000")
    print("\nFeatures enabled:")
    print("  [+] WebSocket support (for collaborative editor)")
    print("  [+] Django Channels")
    print("  [+] Real-time collaboration")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    try:
        # Run Daphne
        subprocess.run([
            sys.executable, "-m", "daphne",
            "-b", "0.0.0.0",
            "-p", "8000",
            "mysite.asgi:application"
        ])
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)

