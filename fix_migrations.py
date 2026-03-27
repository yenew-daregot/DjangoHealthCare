#!/usr/bin/env python
"""
Script to fix migration conflicts and create proper migrations
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

def fix_migrations():
    print("Fixing migration conflicts...")
    
    try:
        # Setup Django
        django.setup()
        
        print("\n1. Creating migrations for users (LABORATORIST role)...")
        execute_from_command_line(['manage.py', 'makemigrations', 'users'])
        
        print("\n2. Creating migrations for labs...")
        execute_from_command_line(['manage.py', 'makemigrations', 'labs'])
        
        print("\n3. Applying all migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("\n✅ Migrations completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
        # If there are conflicts, try to merge
        try:
            print("\n🔄 Attempting to merge conflicting migrations...")
            execute_from_command_line(['manage.py', 'makemigrations', '--merge'])
            execute_from_command_line(['manage.py', 'migrate'])
            print("✅ Merge successful!")
            return True
        except Exception as merge_error:
            print(f"❌ Merge failed: {merge_error}")
            return False

if __name__ == '__main__':
    success = fix_migrations()
    if not success:
        print("\n📋 Manual steps to try:")
        print("1. Delete conflicting migration files")
        print("2. Run: python manage.py makemigrations --empty users")
        print("3. Run: python manage.py makemigrations --empty labs")
        print("4. Edit the empty migrations manually")
        print("5. Run: python manage.py migrate")
        sys.exit(1)