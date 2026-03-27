#!/usr/bin/env python
"""
Script to run Django migrations
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def run_migrations():
    print("Running Django migrations...")
    
    try:
        # First, create migrations for users (to add LABORATORIST role)
        print("\n1. Creating migrations for users...")
        execute_from_command_line(['manage.py', 'makemigrations', 'users'])
        
        # Then create migrations for labs
        print("\n2. Creating migrations for labs...")
        execute_from_command_line(['manage.py', 'makemigrations', 'labs'])
        
        # Apply all migrations
        print("\n3. Applying migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("\n✅ Migrations completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == '__main__':
    success = run_migrations()
    if not success:
        sys.exit(1)