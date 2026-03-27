#!/usr/bin/env python3
"""
Create migration for doctor schedule models
"""
import os
import sys
import django

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import execute_from_command_line

def create_schedule_migration():
    """Create migration for schedule models"""
    print("Creating migration for doctor schedule models...")
    
    try:
        # Create migration
        execute_from_command_line([
            'manage.py', 
            'makemigrations', 
            'doctors',
            '--name', 'add_schedule_models'
        ])
        print("✅ Migration created successfully!")
        
        # Apply migration
        print("Applying migration...")
        execute_from_command_line(['manage.py', 'migrate', 'doctors'])
        print("✅ Migration applied successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating/applying migration: {str(e)}")
        return False

if __name__ == '__main__':
    success = create_schedule_migration()
    if success:
        print("\n🎉 Doctor schedule system is ready!")
        print("You can now use the schedule management features.")
    else:
        print("\n❌ Failed to set up schedule system.")
        print("Please check the error messages above.")