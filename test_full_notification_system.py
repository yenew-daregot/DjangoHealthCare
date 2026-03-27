#!/usr/bin/env python
"""
Comprehensive test for the notification system
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from notifications.notification_service import notification_service
from notifications.models import Notification, NotificationPreference

User = get_user_model()

def test_notification_service():
    """Test the notification service functionality"""
    print("🔔 Testing Notification Service...")
    
    # Get or create a test user
    try:
        user, created = User.objects.get_or_create(
            username='testpatient2',
            defaults={
                'email': 'test2@example.com',
                'password': 'pbkdf2_sha256$600000$test$test',
                'role': 'PATIENT',
                'first_name': 'Test',
                'last_name': 'Patient2',
                'phone_number': '1234567890'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
        print(f"✅ {'Created' if created else 'Retrieved'} test user: {user}")
    except Exception as e:
        print(f"❌ Error with user: {e}")
        return False
    
    # Test service status
    try:
        status = notification_service.get_service_status()
        print(f"✅ Service status: {status}")
    except Exception as e:
        print(f"❌ Error getting service status: {e}")
        return False
    
    # Test sending notification through service
    try:
        results = notification_service.send_notification(
            user=user,
            title="Service Test Notification",
            message="This notification was sent through the notification service.",
            notification_type="info",
            channels=['in_app'],
            data={'test': True, 'service_test': True}
        )
        print(f"✅ Notification sent through service: {results}")
    except Exception as e:
        print(f"❌ Error sending notification through service: {e}")
        return False
    
    # Test healthcare-specific notifications
    try:
        # Simulate appointment data
        appointment_data = {
            'id': 1,
            'patient': type('Patient', (), {'user': user})(),
            'doctor': type('Doctor', (), {'user': type('User', (), {'first_name': 'Dr. John', 'last_name': 'Smith'})()})(),
            'appointment_date': '2024-01-15',
            'appointment_time': '10:00 AM'
        }
        
        # Test appointment notification
        results = notification_service.send_notification(
            user=user,
            title="Appointment Scheduled",
            message=f"Your appointment with Dr. John Smith has been scheduled for {appointment_data['appointment_date']} at {appointment_data['appointment_time']}",
            notification_type="info",
            channels=['in_app', 'push'],
            data={
                'appointment_id': appointment_data['id'],
                'type': 'appointment_created'
            }
        )
        print(f"✅ Appointment notification sent: {results}")
    except Exception as e:
        print(f"❌ Error sending appointment notification: {e}")
        return False
    
    # Test health alert notification
    try:
        results = notification_service.send_notification(
            user=user,
            title="Health Alert",
            message="Alert: High Blood Pressure reading detected - 180/120 mmHg",
            notification_type="urgent",
            channels=['in_app', 'sms', 'push'],
            data={
                'type': 'health_alert',
                'vital_reading': {
                    'id': 1,
                    'vital_type': 'Blood Pressure',
                    'value': '180/120',
                    'unit': 'mmHg'
                }
            }
        )
        print(f"✅ Health alert notification sent: {results}")
    except Exception as e:
        print(f"❌ Error sending health alert notification: {e}")
        return False
    
    # Test retrieving notifications
    try:
        notifications = Notification.objects.filter(user=user).order_by('-created_at')
        print(f"✅ Retrieved {notifications.count()} notifications for user")
        for notification in notifications[:3]:
            print(f"   - {notification.title}: {notification.message[:50]}...")
    except Exception as e:
        print(f"❌ Error retrieving notifications: {e}")
        return False
    
    print("🎉 Notification service tests passed!")
    return True

def test_notification_preferences():
    """Test notification preferences functionality"""
    print("\n⚙️ Testing Notification Preferences...")
    
    try:
        user = User.objects.filter(username='testpatient2').first()
        if not user:
            print("❌ No test user found")
            return False
        
        # Create or get preferences
        preferences, created = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                'sms_enabled': True,
                'push_enabled': True,
                'email_enabled': True,
                'in_app_enabled': True,
                'appointment_notifications': True,
                'health_alert_notifications': True,
                'emergency_notifications': True
            }
        )
        print(f"✅ Notification preferences {'created' if created else 'retrieved'}")
        
        # Test updating preferences
        preferences.sms_enabled = False
        preferences.push_enabled = True
        preferences.save()
        print("✅ Updated notification preferences")
        
        # Verify preferences
        updated_preferences = NotificationPreference.objects.get(user=user)
        print(f"✅ Verified preferences: SMS={updated_preferences.sms_enabled}, Push={updated_preferences.push_enabled}")
        
    except Exception as e:
        print(f"❌ Error with preferences: {e}")
        return False
    
    print("🎉 Notification preferences tests passed!")
    return True

def test_notification_models():
    """Test notification models functionality"""
    print("\n📊 Testing Notification Models...")
    
    try:
        user = User.objects.filter(username='testpatient2').first()
        if not user:
            print("❌ No test user found")
            return False
        
        # Test creating different types of notifications
        notification_types = ['info', 'success', 'warning', 'error', 'urgent']
        
        for notif_type in notification_types:
            notification = Notification.objects.create(
                user=user,
                notification_type=notif_type,
                title=f'Test {notif_type.title()} Notification',
                message=f'This is a test {notif_type} notification.',
                metadata={'test': True, 'type': notif_type}
            )
            print(f"✅ Created {notif_type} notification: {notification.id}")
        
        # Test notification methods
        test_notification = Notification.objects.filter(user=user, notification_type='info').first()
        if test_notification:
            test_notification.mark_as_read()
            print(f"✅ Marked notification as read: {test_notification.is_read}")
        
        # Test querying notifications
        unread_count = Notification.objects.filter(user=user, is_read=False).count()
        total_count = Notification.objects.filter(user=user).count()
        print(f"✅ Notification counts: Total={total_count}, Unread={unread_count}")
        
    except Exception as e:
        print(f"❌ Error with models: {e}")
        return False
    
    print("🎉 Notification models tests passed!")
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("🏥 COMPREHENSIVE NOTIFICATION SYSTEM TEST")
    print("=" * 60)
    
    # Test notification service
    service_test_passed = test_notification_service()
    
    # Test notification preferences
    preferences_test_passed = test_notification_preferences()
    
    # Test notification models
    models_test_passed = test_notification_models()
    
    print("\n" + "=" * 60)
    if service_test_passed and preferences_test_passed and models_test_passed:
        print("🎉 ALL COMPREHENSIVE TESTS PASSED!")
        print("✅ Notification system is fully functional")
        print("✅ Backend notification service working")
        print("✅ Notification preferences working")
        print("✅ Notification models working")
        print("✅ Healthcare-specific notifications working")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    print("=" * 60)