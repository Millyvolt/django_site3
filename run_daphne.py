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

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Django with Daphne ASGI Server")
    print("=" * 60)
    print("Server will be available at:")
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

