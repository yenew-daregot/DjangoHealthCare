#!/usr/bin/env python3

import os
import sys
import django
import json
import requests

# Add the backend directory to Python path
sys.path.append('/workspaces/healthcare-frontend/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from patients.models import Patient
from doctors.models import Doctor

User = get_user_model()

def test_admin_create_patient():
    """Test admin patient creation with correct data structure"""
    
    print("=" * 60)
    print("TESTING ADMIN PATIENT CREATION")
    print("=" * 60)
    
    # Test data with correct nested structure
    patient_data = {
        "user": {
            "username": "testpatient123",
            "email": "testpatient123@example.com",
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
    
    print("Test data:")
    print(json.dumps(patient_data, indent=2))
    
    try:
        # Make API request to admin endpoint
        url = "http://127.0.0.1:8000/api/admin/create-patient/"
        
        # First, create an admin user for authentication
        admin_user, created = User.objects.get_or_create(
            username='testadmin',
            defaults={
                'email': 'admin@test.com',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('adminpass123')
            admin_user.save()
            print(f"✅ Created admin user: {admin_user.username}")
        else:
            print(f"✅ Using existing admin user: {admin_user.username}")
        
        # Get auth token (simulate login)
        from rest_framework.authtoken.models import Token
        token, created = Token.objects.get_or_create(user=admin_user)
        
        headers = {
            'Authorization': f'Token {token.key}',
            'Content-Type': 'application/json'
        }
        
        print(f"\n🔑 Using auth token: {token.key[:10]}...")
        print(f"📡 Making request to: {url}")
        
        response = requests.post(url, json=patient_data, headers=headers)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"📊 Response Data:")
            print(json.dumps(response_data, indent=2))
        except:
            print(f"📊 Response Text: {response.text}")
        
        if response.status_code == 201:
            print("✅ SUCCESS: Patient created successfully!")
            
            # Verify in database
            try:
                user = User.objects.get(username="testpatient123")
                patient = Patient.objects.get(user=user)
                print(f"✅ Verified in DB - User ID: {user.id}, Patient ID: {patient.id}")
            except Exception as e:
                print(f"❌ DB Verification failed: {e}")
                
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

def test_admin_create_doctor():
    """Test admin doctor creation with correct data structure"""
    
    print("\n" + "=" * 60)
    print("TESTING ADMIN DOCTOR CREATION")
    print("=" * 60)
    
    # Test data with correct nested structure
    doctor_data = {
        "user": {
            "username": "testdoctor123",
            "email": "testdoctor123@example.com",
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
    
    print("Test data:")
    print(json.dumps(doctor_data, indent=2))
    
    try:
        # Make API request to admin endpoint
        url = "http://127.0.0.1:8000/api/admin/create-doctor/"
        
        # Get admin user
        admin_user = User.objects.get(username='testadmin')
        from rest_framework.authtoken.models import Token
        token = Token.objects.get(user=admin_user)
        
        headers = {
            'Authorization': f'Token {token.key}',
            'Content-Type': 'application/json'
        }
        
        print(f"\n🔑 Using auth token: {token.key[:10]}...")
        print(f"📡 Making request to: {url}")
        
        response = requests.post(url, json=doctor_data, headers=headers)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"📊 Response Data:")
            print(json.dumps(response_data, indent=2))
        except:
            print(f"📊 Response Text: {response.text}")
        
        if response.status_code == 201:
            print("✅ SUCCESS: Doctor created successfully!")
            
            # Verify in database
            try:
                user = User.objects.get(username="testdoctor123")
                doctor = Doctor.objects.get(user=user)
                print(f"✅ Verified in DB - User ID: {user.id}, Doctor ID: {doctor.id}")
            except Exception as e:
                print(f"❌ DB Verification failed: {e}")
                
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

def cleanup_test_data():
    """Clean up test data"""
    print("\n" + "=" * 60)
    print("CLEANING UP TEST DATA")
    print("=" * 60)
    
    try:
        # Delete test users
        test_users = User.objects.filter(username__in=['testpatient123', 'testdoctor123'])
        count = test_users.count()
        test_users.delete()
        print(f"✅ Deleted {count} test users")
        
    except Exception as e:
        print(f"❌ Cleanup error: {e}")

if __name__ == '__main__':
    try:
        test_admin_create_patient()
        test_admin_create_doctor()
    finally:
        cleanup_test_data()