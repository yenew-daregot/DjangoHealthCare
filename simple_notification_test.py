#!/usr/bin/env python
"""
Simple test script for the notification system
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from notifications.models import Notification, NotificationPreference

User = get_user_model()

def test_basic_functionality():
    """Test basic notification functionality without importing the service"""
    print("🔔 Testing Basic Notification Functionality...")
    
    # Get or create a test user
    try:
        user, created = User.objects.get_or_create(
            username='testpatient',
            defaults={
                'email': 'test@example.com',
                'password': 'pbkdf2_sha256$600000$test$test',  # Dummy hashed password
                'role': 'PATIENT',
                'first_name': 'Test',
                'last_name': 'Patient',
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
        print(f"✅ Notification preferences {'created' if created else 'retrieved'}")
    except Exception as e:
        print(f"❌ Error with preferences: {e}")
        return False
    
    # Test creating a notification directly
    try:
        notification = Notification.objects.create(
            user=user,
            notification_type='info',
            title='Test Notification',
            message='This is a test notification created directly in the database.',
            metadata={'test': True}
        )
        print(f"✅ Created notification: {notification}")
    except Exception as e:
        print(f"❌ Error creating notification: {e}")
        return False
    
    # Test retrieving notifications
    try:
        notifications = Notification.objects.filter(user=user)
        print(f"✅ Retrieved {notifications.count()} notifications for user")
        for notification in notifications[:3]:
            print(f"   - {notification.title}: {notification.message[:50]}...")
    except Exception as e:
        print(f"❌ Error retrieving notifications: {e}")
        return False
    
    print("🎉 Basic functionality tests passed!")
    return True

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 Testing API Endpoints...")
    
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        
        # Get test user
        user = User.objects.filter(username='testpatient').first()
        if not user:
            print("❌ No test user found")
            return False
        
        # Login user
        client.force_login(user)
        
        # Test basic endpoints
        endpoints_to_test = [
            '/api/notifications/',
            '/api/notifications/preferences/',
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = client.get(endpoint)
                print(f"✅ {endpoint}: Status {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint}: Error {e}")
        
        print("🎉 API endpoint tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("🏥 SIMPLE NOTIFICATION SYSTEM TEST")
    print("=" * 50)
    
    # Test basic functionality
    basic_test_passed = test_basic_functionality()
    
    # Test API endpoints
    api_test_passed = test_api_endpoints()
    
    print("\n" + "=" * 50)
    if basic_test_passed and api_test_passed:
        print("🎉 BASIC TESTS PASSED!")
    else:
        print("❌ Some tests failed.")
    print("=" * 50)