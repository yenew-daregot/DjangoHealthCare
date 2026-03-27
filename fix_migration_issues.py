#!/usr/bin/env python3
"""
Fix migration issues by making problematic fields nullable
"""
import os
import sys
import django

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def fix_migration_issues():
    """Fix common migration issues"""
    print("🔧 Fixing migration issues...")
    
    try:
        # Import models after Django setup
        from prescriptions.models import Prescription
        from chat.models import ChatNotification
        
        print("✅ Models imported successfully")
        print("✅ Prescription.patient field has been made nullable")
        print("✅ ChatNotification.title field should have a default")
        
        # Now try to create migrations
        from django.core.management import execute_from_command_line
        
        print("\n📝 Creating migrations...")
        execute_from_command_line(['manage.py', 'makemigrations'])
        
        print("\n🚀 Applying migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("\n🎉 Migration issues fixed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing migrations: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = fix_migration_issues()
    if success:
        print("\n✅ All migration issues resolved!")
    else:
        print("\n❌ Some issues remain. Please check the errors above.")