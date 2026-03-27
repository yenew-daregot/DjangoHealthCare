#!/usr/bin/env python3

import os
import sys
import django
import json

# Add the backend directory to Python path
sys.path.append('/workspaces/healthcare-frontend/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

def test_admin_endpoints():
    """Test admin endpoints using Django test client"""
    
    print("=" * 60)
    print("TESTING ADMIN ENDPOINTS WITH DJANGO CLIENT")
    print("=" * 60)
    
    # Create test client
    client = Client()
    
    # Create admin user
    try:
        admin_user = User.objects.get(username='testadmin')
        print(f"✅ Using existing admin user: {admin_user.username}")
    except User.DoesNotExist:
        admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='adminpass123',
            role='ADMIN',
            is_staff=True,
            is_superuser=True
        )
        print(f"✅ Created admin user: {admin_user.username}")
    
    # Get or create token
    token, created = Token.objects.get_or_create(user=admin_user)
    print(f"🔑 Auth token: {token.key[:10]}...")
    
    # Test patient creation
    print("\n📝 Testing patient creation...")
    patient_data = {
        "user": {
            "username": "testpatient456",
            "email": "testpatient456@example.com",
            "password": "testpassword123",
            "confirm_password": "testpassword123",
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
    
    response = client.post(
        '/api/admin/create-patient/',
        data=json.dumps(patient_data),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Token {token.key}'
    )
    
    print(f"📊 Patient Creation Response Status: {response.status_code}")
    try:
        response_data = response.json()
        print(f"📊 Patient Response Data:")
        print(json.dumps(response_data, indent=2))
    except:
        print(f"📊 Patient Response Content: {response.content.decode()}")
    
    # Test doctor creation
    print("\n📝 Testing doctor creation...")
    doctor_data = {
        "user": {
            "username": "testdoctor456",
            "email": "testdoctor456@example.com",
            "password": "testpassword123",
            "confirm_password": "testpassword123",
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
    
    response = client.post(
        '/api/admin/create-doctor/',
        data=json.dumps(doctor_data),
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Token {token.key}'
    )
    
    print(f"📊 Doctor Creation Response Status: {response.status_code}")
    try:
        response_data = response.json()
        print(f"📊 Doctor Response Data:")
        print(json.dumps(response_data, indent=2))
    except:
        print(f"📊 Doctor Response Content: {response.content.decode()}")
    
    # Clean up
    print("\n🧹 Cleaning up test data...")
    try:
        User.objects.filter(username__in=['testpatient456', 'testdoctor456']).delete()
        print("✅ Cleanup completed")
    except Exception as e:
        print(f"❌ Cleanup error: {e}")

if __name__ == '__main__':
    test_admin_endpoints()