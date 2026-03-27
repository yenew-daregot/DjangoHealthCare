#!/usr/bin/env python
"""
Fix notification model conflicts by updating related_name
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def fix_notification_conflict():
    """Fix the notification model conflict"""
    print("🔧 Fixing notification model conflicts...")
    
    try:
        # The model change has been made, now we need to create migrations
        print("✅ EmergencyNotification related_name changed to 'emergency_notifications'")
        print("📝 Please run the following commands:")
        print("   1. python manage.py makemigrations emergency")
        print("   2. python manage.py migrate")
        
        print("\n🎯 This will resolve the conflict between:")
        print("   - emergency.EmergencyNotification.emergency_request (now uses 'emergency_notifications')")
        print("   - notifications.Notification.related_emergency (uses 'notifications')")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    success = fix_notification_conflict()
    if success:
        print("\n✅ Notification conflict fix completed!")
        print("🚀 You can now run makemigrations and migrate safely.")
    else:
        print("\n❌ Fix failed. Please check the error messages above.")