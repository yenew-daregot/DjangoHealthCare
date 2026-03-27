#!/usr/bin/env python3
"""
Test Emergency API Endpoints
Tests all emergency-related endpoints to ensure they're working correctly.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from patients.models import Patient
from doctors.models import Doctor
from emergency.models import EmergencyRequest, EmergencyContact
import json

User = get_user_model()

def create_test_data():
    """Create test data for emergency endpoints"""
    print("Creating test data...")
    
    # Create test patient
    patient_user = User.objects.create_user(
        username='testpatient',
        email='patient@test.com',
        password='testpass123',
        role='PATIENT',
        first_name='Test',
        last_name='Patient',
        phone='+1234567890'
    )
    
    patient, created = Patient.objects.get_or_create(
        user=patient_user,
        defaults={
            'date_of_birth': '1990-01-01',
            'gender': 'M',
            'blood_type': 'O+',
            'allergies': 'None',
            'medical_history': 'No significant history'
        }
    )
    
    # Create test doctor
    doctor_user = User.objects.create_user(
        username='testdoctor',
        email='doctor@test.com',
        password='testpass123',
        role='DOCTOR',
        first_name='Test',
        last_name='Doctor',
        phone='+1234567891'
    )
    
    doctor, created = Doctor.objects.get_or_create(
        user=doctor_user,
        defaults={
            'specialization': 'Emergency Medicine',
            'license_number': 'DOC123456',
            'years_of_experience': 10
        }
    )
    
    # Create test admin
    admin_user = User.objects.create_user(
        username='testadmin',
        email='admin@test.com',
        password='testpass123',
        role='ADMIN',
        first_name='Test',
        last_name='Admin',
        is_staff=True,
        is_superuser=True
    )
    
    # Create emergency contact
    emergency_contact = EmergencyContact.objects.create(
        patient=patient,
        name='Emergency Contact',
        relationship='spouse',
        phone_number='+1234567892',
        email='emergency@test.com',
        is_primary=True
    )
    
    # Create test emergency requests with valid dates
    now = timezone.now()
    
    emergency1 = EmergencyRequest.objects.create(
        patient=patient,
        location='123 Test Street, Test City',
        latitude=40.7128,
        longitude=-74.0060,
        description='Test emergency - chest pain',
        emergency_type='cardiac',
        priority='critical',
        status='pending',
        created_at=now - timedelta(minutes=30),
        patient_age=33,
        patient_blood_type='O+',
        medical_notes='Patient has history of heart disease'
    )
    
    emergency2 = EmergencyRequest.objects.create(
        patient=patient,
        location='456 Test Avenue, Test City',
        latitude=40.7589,
        longitude=-73.9851,
        description='Test emergency - severe allergic reaction',
        emergency_type='medical',
        priority='high',
        status='acknowledged',
        created_at=now - timedelta(hours=1),
        acknowledged_at=now - timedelta(minutes=45),
        assigned_doctor=doctor,
        patient_age=33,
        patient_blood_type='O+',
        patient_allergies='Peanuts',
        medical_notes='Known severe peanut allergy'
    )
    
    emergency3 = EmergencyRequest.objects.create(
        patient=patient,
        location='789 Test Boulevard, Test City',
        latitude=40.7831,
        longitude=-73.9712,
        description='Test emergency - minor injury',
        emergency_type='trauma',
        priority='low',
        status='completed',
        created_at=now - timedelta(hours=2),
        acknowledged_at=now - timedelta(hours=2) + timedelta(minutes=5),
        completed_at=now - timedelta(hours=1),
        patient_age=33,
        patient_blood_type='O+',
        response_notes='Patient treated and released'
    )
    
    print(f"Created test data:")
    print(f"- Patient: {patient.user.get_full_name()} ({patient.user.email})")
    print(f"- Doctor: {doctor.user.get_full_name()} ({doctor.user.email})")
    print(f"- Admin: {admin_user.get_full_name()} ({admin_user.email})")
    print(f"- Emergency Requests: {EmergencyRequest.objects.count()}")
    print(f"- Emergency Contacts: {EmergencyContact.objects.count()}")
    
    return {
        'patient_user': patient_user,
        'doctor_user': doctor_user,
        'admin_user': admin_user,
        'patient': patient,
        'doctor': doctor,
        'emergencies': [emergency1, emergency2, emergency3]
    }

def test_emergency_endpoints():
    """Test all emergency endpoints"""
    print("\n" + "="*50)
    print("TESTING EMERGENCY API ENDPOINTS")
    print("="*50)
    
    # Create test data
    test_data = create_test_data()
    client = Client()
    
    # Test endpoints without authentication first
    print("\n1. Testing Emergency Endpoints (No Auth)")
    print("-" * 40)
    
    # Test emergency requests list
    response = client.get('/api/emergency/requests/')
    print(f"GET /api/emergency/requests/ - Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Response type: {type(data)}")
        if isinstance(data, dict):
            print(f"  Keys: {list(data.keys())}")
            if 'results' in data:
                print(f"  Results count: {len(data['results'])}")
        elif isinstance(data, list):
            print(f"  Results count: {len(data)}")
    
    # Test with patient authentication
    print("\n2. Testing with Patient Authentication")
    print("-" * 40)
    
    client.login(username='testpatient', password='testpass123')
    
    response = client.get('/api/emergency/requests/')
    print(f"GET /api/emergency/requests/ (Patient) - Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Data structure: {type(data)}")
        if isinstance(data, dict) and 'results' in data:
            print(f"  Emergency count: {len(data['results'])}")
            if data['results']:
                emergency = data['results'][0]
                print(f"  Sample emergency ID: {emergency.get('request_id', emergency.get('id'))}")
                print(f"  Sample emergency type: {emergency.get('emergency_type')}")
                print(f"  Sample emergency status: {emergency.get('status')}")
                print(f"  Sample emergency created_at: {emergency.get('created_at')}")
        elif isinstance(data, list):
            print(f"  Emergency count: {len(data)}")
    
    # Test emergency contacts
    response = client.get('/api/emergency/contacts/')
    print(f"GET /api/emergency/contacts/ (Patient) - Status: {response.status_code}")
    
    client.logout()
    
    # Test with doctor authentication
    print("\n3. Testing with Doctor Authentication")
    print("-" * 40)
    
    client.login(username='testdoctor', password='testpass123')
    
    response = client.get('/api/emergency/requests/')
    print(f"GET /api/emergency/requests/ (Doctor) - Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, dict) and 'results' in data:
            print(f"  Emergency count (Doctor view): {len(data['results'])}")
        elif isinstance(data, list):
            print(f"  Emergency count (Doctor view): {len(data)}")
    
    client.logout()
    
    # Test with admin authentication
    print("\n4. Testing with Admin Authentication")
    print("-" * 40)
    
    client.login(username='testadmin', password='testpass123')
    
    # Test admin emergency endpoints
    response = client.get('/api/emergency/admin/requests/')
    print(f"GET /api/emergency/admin/requests/ (Admin) - Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, dict) and 'results' in data:
            print(f"  Admin emergency count: {len(data['results'])}")
            if 'stats' in data:
                print(f"  Stats: {data['stats']}")
        elif isinstance(data, list):
            print(f"  Admin emergency count: {len(data)}")
    
    # Test emergency statistics
    response = client.get('/api/admin/emergency-statistics/')
    print(f"GET /api/admin/emergency-statistics/ (Admin) - Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Statistics keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
    
    client.logout()
    
    # Test date validation
    print("\n5. Testing Date Validation")
    print("-" * 40)
    
    emergencies = EmergencyRequest.objects.all()
    for emergency in emergencies:
        print(f"Emergency {emergency.request_id}:")
        print(f"  created_at: {emergency.created_at} (type: {type(emergency.created_at)})")
        print(f"  acknowledged_at: {emergency.acknowledged_at} (type: {type(emergency.acknowledged_at)})")
        
        # Test date formatting
        try:
            if emergency.created_at:
                formatted = emergency.created_at.strftime('%Y-%m-%d %H:%M:%S')
                print(f"  formatted created_at: {formatted}")
        except Exception as e:
            print(f"  ERROR formatting created_at: {e}")
        
        try:
            if emergency.acknowledged_at:
                formatted = emergency.acknowledged_at.strftime('%Y-%m-%d %H:%M:%S')
                print(f"  formatted acknowledged_at: {formatted}")
        except Exception as e:
            print(f"  ERROR formatting acknowledged_at: {e}")

def test_api_response_format():
    """Test the format of API responses"""
    print("\n6. Testing API Response Format")
    print("-" * 40)
    
    client = Client()
    
    # Test as patient
    client.login(username='testpatient', password='testpass123')
    response = client.get('/api/emergency/requests/')
    
    if response.status_code == 200:
        data = response.json()
        print("API Response Analysis:")
        print(f"  Response type: {type(data)}")
        
        if isinstance(data, dict):
            print(f"  Top-level keys: {list(data.keys())}")
            
            if 'results' in data:
                results = data['results']
                print(f"  Results type: {type(results)}")
                print(f"  Results count: {len(results) if isinstance(results, list) else 'Not a list'}")
                
                if isinstance(results, list) and results:
                    sample = results[0]
                    print(f"  Sample emergency keys: {list(sample.keys()) if isinstance(sample, dict) else 'Not a dict'}")
                    
                    # Check date fields
                    date_fields = ['created_at', 'acknowledged_at', 'dispatched_at', 'completed_at']
                    for field in date_fields:
                        if field in sample:
                            value = sample[field]
                            print(f"    {field}: {value} (type: {type(value)})")
            
            if 'stats' in data:
                print(f"  Stats: {data['stats']}")
        
        elif isinstance(data, list):
            print(f"  Direct list with {len(data)} items")
            if data:
                sample = data[0]
                print(f"  Sample emergency keys: {list(sample.keys()) if isinstance(sample, dict) else 'Not a dict'}")

if __name__ == '__main__':
    try:
        test_emergency_endpoints()
        test_api_response_format()
        print("\n" + "="*50)
        print("EMERGENCY ENDPOINT TESTING COMPLETED")
        print("="*50)
        
    except Exception as e:
        print(f"\nERROR during testing: {e}")
        import traceback
        traceback.print_exc()