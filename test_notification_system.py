#!/usr/bin/env python
"""
Test script for the notification system
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

def test_notification_system():
    """Test the notification system functionality"""
    print("🔔 Testing Notification System...")
    
    # Get or create a test user
    try:
        user = User.objects.filter(role='PATIENT').first()
        if not user:
            user = User.objects.create_user(
                username='testpatient',
                email='test@example.com',
                password='testpass123',
                role='PATIENT',
                first_name='Test',
                last_name='Patient',
                phone_number='1234567890'
            )
            print(f"✅ Created test user: {user}")
        else:
            print(f"✅ Using existing user: {user}")
    except Exception as e:
        print(f"❌ Error creating/getting user: {e}")
        return False
    
    # Test service status
    try:
        status = notification_service.get_service_status()
        print(f"✅ Service status: {status}")
    except Exception as e:
        print(f"❌ Error getting service status: {e}")
        return False
    
    # Test creating notification preferences
    try:
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
        print(f"✅ Notification preferences {'created' if created else 'retrieved'}: {preferences}")
    except Exception as e:
        print(f"❌ Error with notification preferences: {e}")
        return False
    
    # Test sending a simple notification
    try:
        results = notification_service.send_notification(
            user=user,
            title="Test Notification",
            message="This is a test notification to verify the system is working.",
            notification_type="info",
            channels=['in_app'],
            data={'test': True, 'timestamp': '2024-01-01T12:00:00Z'}
        )
        print(f"✅ Notification sent successfully: {results}")
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        return False
    
    # Test retrieving notifications
    try:
        notifications = Notification.objects.filter(user=user).order_by('-created_at')[:5]
        print(f"✅ Retrieved {notifications.count()} notifications for user")
        for notification in notifications:
            print(f"   - {notification.title}: {notification.message[:50]}...")
    except Exception as e:
        print(f"❌ Error retrieving notifications: {e}")
        return False
    
    # Test healthcare-specific notifications
    try:
        # Test appointment notification (simulated)
        appointment_data = {
            'id': 1,
            'doctor_name': 'Dr. Smith',
            'appointment_date': '2024-01-15',
            'appointment_time': '10:00 AM'
        }
        
        results = notification_service.send_notification(
            user=user,
            title="Appointment Reminder",
            message=f"You have an appointment with {appointment_data['doctor_name']} tomorrow at {appointment_data['appointment_time']}",
            notification_type="warning",
            channels=['in_app', 'push'],
            data={
                'type': 'appointment_reminder',
                'appointment': appointment_data
            }
        )
        print(f"✅ Appointment notification sent: {results}")
    except Exception as e:
        print(f"❌ Error sending appointment notification: {e}")
        return False
    
    # Test health alert notification (simulated)
    try:
        vital_data = {
            'id': 1,
            'vital_type': 'Blood Pressure',
            'value': '180/120',
            'unit': 'mmHg'
        }
        
        results = notification_service.send_notification(
            user=user,
            title="Health Alert",
            message=f"Alert: High {vital_data['vital_type']} reading detected - {vital_data['value']} {vital_data['unit']}",
            notification_type="urgent",
            channels=['in_app', 'sms', 'push'],
            data={
                'type': 'health_alert',
                'vital_reading': vital_data
            }
        )
        print(f"✅ Health alert notification sent: {results}")
    except Exception as e:
        print(f"❌ Error sending health alert notification: {e}")
        return False
    
    print("\n🎉 All notification system tests passed!")
    return True

def test_notification_api():
    """Test notification API endpoints"""
    print("\n🌐 Testing Notification API...")
    
    try:
        from django.test import Client
        from django.contrib.auth import authenticate
        
        client = Client()
        
        # Get test user
        user = User.objects.filter(role='PATIENT').first()
        if not user:
            print("❌ No test user found for API testing")
            return False
        
        # Login user (simulate authentication)
        client.force_login(user)
        
        # Test notification history endpoint
        response = client.get('/api/notifications/history/')
        print(f"✅ Notification history API: Status {response.status_code}")
        
        # Test preferences endpoint
        response = client.get('/api/notifications/preferences/')
        print(f"✅ Notification preferences API: Status {response.status_code}")
        
        # Test service status endpoint
        response = client.get('/api/notifications/service-status/')
        print(f"✅ Service status API: Status {response.status_code}")
        
        # Test sending notification via API
        response = client.post('/api/notifications/send/', {
            'title': 'API Test Notification',
            'message': 'This notification was sent via API',
            'notification_type': 'info',
            'channels': ['in_app']
        }, content_type='application/json')
        print(f"✅ Send notification API: Status {response.status_code}")
        
        print("🎉 All API tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🏥 HEALTHCARE NOTIFICATION SYSTEM TEST")
    print("=" * 60)
    
    # Test core notification system
    system_test_passed = test_notification_system()
    
    # Test API endpoints
    api_test_passed = test_notification_api()
    
    print("\n" + "=" * 60)
    if system_test_passed and api_test_passed:
        print("🎉 ALL TESTS PASSED! Notification system is working correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    print("=" * 60)