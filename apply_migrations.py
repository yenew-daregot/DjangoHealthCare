#!/usr/bin/env python
"""
Simple script to apply migrations without interactive prompts
"""
import os
import sys
import django
from django.core.management import call_command

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def apply_migrations():
    print("Applying migrations...")
    
    try:
        print("\n1. Applying users migrations...")
        call_command('migrate', 'users', verbosity=2, interactive=False)
        
        print("\n2. Applying labs migrations...")
        call_command('migrate', 'labs', verbosity=2, interactive=False)
        
        print("\n3. Applying all remaining migrations...")
        call_command('migrate', verbosity=2, interactive=False)
        
        print("\n✅ All migrations applied successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

if __name__ == '__main__':
    success = apply_migrations()
    if not success:
        sys.exit(1)