#!/usr/bin/env python3

import os
import sys
import django
import requests
import json

# Add the backend directory to Python path
sys.path.append('/workspaces/healthcare-frontend/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

def test_admin_api_endpoints():
    """Test admin API endpoints with proper authentication"""
    
    print("=" * 60)
    print("TESTING ADMIN API ENDPOINTS")
    print("=" * 60)
    
    # Create or get admin user
    try:
        admin_user = User.objects.get(username='admin')
        print(f"✅ Using existing admin user: {admin_user.username}")
    except User.DoesNotExist:
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            role='ADMIN',
            is_staff=True,
            is_superuser=True
        )
        print(f"✅ Created admin user: {admin_user.username}")
    
    # Get or create token
    token, created = Token.objects.get_or_create(user=admin_user)
    print(f"🔑 Admin token: {token.key[:10]}...")
    
    # Test endpoints
    base_url = "http://127.0.0.1:8000/api/"
    headers = {
        'Authorization': f'Token {token.key}',
        'Content-Type': 'application/json'
    }
    
    # Test 1: Basic API connection
    print("\n📡 Testing basic API connection...")
    try:
        response = requests.get(f"{base_url}test/", headers=headers, timeout=5)
        print(f"✅ API Test: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ API Test failed: {e}")
    
    # Test 2: Admin create patient endpoint
    print("\n📡 Testing admin create patient endpoint...")
    patient_data = {
        "user": {
            "username": "testpatient123",
            "email": "testpatient123@example.com",
            "password": "testpass123",
            "confirm_password": "testpass123",
            "first_name": "Test",
            "last_name": "Patient",
            "phone_number": "1234567890",
            "address": "123 Test Street"
        },
        "age": 30,
        "gender": "male",
        "blood_group": "A+",
        "emergency_contact": "Emergency Contact",
        "emergency_contact_phone": "0987654321",
        "insurance_id": "INS123456",
        "allergy_notes": "No known allergies",
        "chronic_conditions": "None",
        "height": 175.5,
        "weight": 70.0
    }
    
    try:
        response = requests.post(
            f"{base_url}admin/create-patient/",
            json=patient_data,
            headers=headers,
            timeout=10
        )
        print(f"📊 Create Patient Response: {response.status_code}")
        if response.status_code == 201:
            print(f"✅ Patient created successfully: {response.json()}")
        else:
            print(f"❌ Patient creation failed: {response.text}")
    except Exception as e:
        print(f"❌ Patient creation error: {e}")
    
    # Test 3: Admin create doctor endpoint
    print("\n📡 Testing admin create doctor endpoint...")
    doctor_data = {
        "user": {
            "username": "testdoctor123",
            "email": "testdoctor123@example.com",
            "password": "testpass123",
            "confirm_password": "testpass123",
            "first_name": "Test",
            "last_name": "Doctor",
            "phone_number": "1234567890",
            "address": "123 Doctor Street"
        },
        "specialization": "General Medicine",
        "license_number": "LIC123456",
        "qualification": "MBBS, MD",
        "years_of_experience": 5,
        "consultation_fee": 100.0,
        "bio": "Experienced general practitioner",
        "is_available": True,
        "is_verified": True
    }
    
    try:
        response = requests.post(
            f"{base_url}admin/create-doctor/",
            json=doctor_data,
            headers=headers,
            timeout=10
        )
        print(f"📊 Create Doctor Response: {response.status_code}")
        if response.status_code == 201:
            print(f"✅ Doctor created successfully: {response.json()}")
        else:
            print(f"❌ Doctor creation failed: {response.text}")
    except Exception as e:
        print(f"❌ Doctor creation error: {e}")
    
    # Clean up test data
    print("\n🧹 Cleaning up test data...")
    try:
        User.objects.filter(username__in=['testpatient123', 'testdoctor123']).delete()
        print("✅ Test data cleaned up")
    except Exception as e:
        print(f"❌ Cleanup error: {e}")

if __name__ == '__main__':
    test_admin_api_endpoints()