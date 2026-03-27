#!/usr/bin/env python
"""
Test the doctor profile API endpoint
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from doctors.models import Doctor

User = get_user_model()

def test_doctor_profile_api():
    """Test the doctor profile API endpoint"""
    print("🔍 Testing Doctor Profile API...")
    
    # Get a doctor user
    try:
        doctor_user = User.objects.filter(role='DOCTOR').first()
        if not doctor_user:
            print("❌ No doctor users found")
            return False
        
        print(f"✅ Testing with doctor user: {doctor_user.username} ({doctor_user.email})")
        
        # Check if they have a doctor profile
        try:
            doctor = Doctor.objects.get(user=doctor_user)
            print(f"✅ Doctor profile exists: {doctor.full_name}")
        except Doctor.DoesNotExist:
            print("❌ No doctor profile found for this user")
            return False
        
        # Test the API endpoint
        client = Client()
        client.force_login(doctor_user)
        
        # Test GET request
        response = client.get('/api/doctors/profile/')
        print(f"✅ GET /api/doctors/profile/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Profile data received:")
            print(f"   - Name: {data.get('first_name', '')} {data.get('last_name', '')}")
            print(f"   - Email: {data.get('email', 'N/A')}")
            print(f"   - Specialization: {data.get('specialization', 'N/A')}")
            print(f"   - Available: {data.get('is_available', False)}")
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error details: {error_data}")
            except:
                print(f"   Response content: {response.content}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

def test_multiple_doctors():
    """Test API with multiple doctor users"""
    print("\n🔍 Testing Multiple Doctor Users...")
    
    doctor_users = User.objects.filter(role='DOCTOR')[:5]  # Test first 5
    
    for user in doctor_users:
        print(f"\n--- Testing user: {user.username} ---")
        
        try:
            doctor = Doctor.objects.get(user=user)
            print(f"✅ Has doctor profile: {doctor.full_name}")
            
            # Test API
            client = Client()
            client.force_login(user)
            response = client.get('/api/doctors/profile/')
            
            if response.status_code == 200:
                print(f"✅ API works for {user.username}")
            else:
                print(f"❌ API failed for {user.username}: {response.status_code}")
                
        except Doctor.DoesNotExist:
            print(f"❌ No doctor profile for {user.username}")
        except Exception as e:
            print(f"❌ Error testing {user.username}: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("🏥 DOCTOR PROFILE API TEST")
    print("=" * 60)
    
    # Test single doctor
    api_works = test_doctor_profile_api()
    
    # Test multiple doctors
    test_multiple_doctors()
    
    print("\n" + "=" * 60)
    if api_works:
        print("✅ Doctor Profile API is working!")
        print("The issue might be:")
        print("1. Frontend authentication token issue")
        print("2. User not logged in as a doctor")
        print("3. Network/CORS issue")
    else:
        print("❌ Doctor Profile API has issues")
        print("Check the backend logs for more details")
    print("=" * 60)