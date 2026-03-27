#!/usr/bin/env python
"""
Test script for Quick SOS functionality
"""
import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth import get_user_model
from patients.models import Patient
from emergency.models import EmergencyRequest
from rest_framework.test import APIClient
from rest_framework import status
import json

User = get_user_model()

def test_quick_sos():
    """Test the Quick SOS endpoint"""
    print("🧪 Testing Quick SOS functionality...")
    
    # Create test user and patient
    try:
        user = User.objects.create_user(
            username='testpatient',
            email='test@example.com',
            password='testpass123',
            role='PATIENT'
        )
        print(f"✅ Created test user: {user.username}")
        
        patient = Patient.objects.create(
            user=user,
            age=30,
            gender='male'
        )
        print(f"✅ Created test patient: {patient}")
        
        # Test API endpoint
        client = APIClient()
        
        # Login to get token
        login_response = client.post('/api/auth/token/', {
            'username': 'testpatient',
            'password': 'testpass123'
        })
        
        if login_response.status_code == 200:
            token = login_response.data['access']
            print(f"✅ Got auth token")
            
            # Test Quick SOS
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
            sos_response = client.post('/api/emergency/mobile/quick-sos/')
            
            print(f"📡 Quick SOS Response Status: {sos_response.status_code}")
            print(f"📡 Quick SOS Response Data: {sos_response.data}")
            
            if sos_response.status_code == 200:
                print("✅ Quick SOS test PASSED!")
                return True
            else:
                print(f"❌ Quick SOS test FAILED: {sos_response.data}")
                return False
        else:
            print(f"❌ Login failed: {login_response.data}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            EmergencyRequest.objects.filter(patient__user__username='testpatient').delete()
            Patient.objects.filter(user__username='testpatient').delete()
            User.objects.filter(username='testpatient').delete()
            print("🧹 Cleaned up test data")
        except:
            pass

def check_emergency_models():
    """Check if emergency models are properly set up"""
    print("🔍 Checking emergency models...")
    
    try:
        from emergency.models import EmergencyRequest, EmergencyContact
        print("✅ Emergency models imported successfully")
        
        # Check if tables exist
        print(f"📊 EmergencyRequest table exists: {EmergencyRequest._meta.db_table}")
        print(f"📊 EmergencyContact table exists: {EmergencyContact._meta.db_table}")
        
        return True
    except Exception as e:
        print(f"❌ Emergency models check failed: {e}")
        return False

def check_patient_models():
    """Check if patient models are properly set up"""
    print("🔍 Checking patient models...")
    
    try:
        from patients.models import Patient
        print("✅ Patient model imported successfully")
        
        # Check if there are any patients
        patient_count = Patient.objects.count()
        print(f"📊 Total patients in database: {patient_count}")
        
        return True
    except Exception as e:
        print(f"❌ Patient models check failed: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Starting Quick SOS tests...\n")
    
    # Run checks
    models_ok = check_emergency_models() and check_patient_models()
    
    if models_ok:
        # Run the actual test
        success = test_quick_sos()
        
        if success:
            print("\n🎉 All tests passed!")
        else:
            print("\n💥 Some tests failed!")
    else:
        print("\n💥 Model setup issues detected!")