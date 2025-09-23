#!/usr/bin/env python
"""
Script to run Django development server with debug toolbar support
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
    from django.core.management import execute_from_command_line
    
    # Run Django development server
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
