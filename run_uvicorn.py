#!/usr/bin/env python
"""
Script to run Django with Uvicorn ASGI server
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# Setup Django
django.setup()

if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "mysite.asgi:application",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )
