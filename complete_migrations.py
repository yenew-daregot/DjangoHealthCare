#!/usr/bin/env python
"""
Complete migrations script to handle all pending migrations
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from django.utils import timezone

def check_migration_status():
    """Check current migration status"""
    print("Checking migration status...")
    try:
        call_command('showmigrations', verbosity=1)
    except Exception as e:
        print(f"Error checking migrations: {e}")

def apply_migrations():
    """Apply all pending migrations"""
    print("\nApplying migrations...")
    try:
        # First, try to migrate without making new migrations
        call_command('migrate', verbosity=2)
        print("✅ All migrations applied successfully!")
        return True
    except Exception as e:
        print(f"❌ Error applying migrations: {e}")
        return False

def make_migrations():
    """Make new migrations for all apps"""
    print("\nMaking new migrations...")
    try:
        # Make migrations for specific apps that have changes
        apps_to_migrate = ['doctors', 'prescriptions', 'chat']
        
        for app in apps_to_migrate:
            print(f"\nMaking migrations for {app}...")
            call_command('makemigrations', app, verbosity=2)
        
        print("✅ New migrations created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error making migrations: {e}")
        return False

def main():
    print("🏥 Healthcare System Migration Completion Script")
    print("=" * 50)
    
    # Check current status
    check_migration_status()
    
    # Try to apply existing migrations first
    if apply_migrations():
        print("\n✅ All migrations completed successfully!")
        return
    
    # If that fails, make new migrations and then apply
    print("\n⚠️  Some migrations failed. Creating new migrations...")
    
    if make_migrations():
        print("\n🔄 Applying new migrations...")
        if apply_migrations():
            print("\n✅ All migrations completed successfully!")
        else:
            print("\n❌ Failed to apply new migrations. Manual intervention required.")
    else:
        print("\n❌ Failed to create new migrations. Manual intervention required.")
    
    # Final status check
    print("\n" + "=" * 50)
    print("Final migration status:")
    check_migration_status()

if __name__ == '__main__':
    main()