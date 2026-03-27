#!/usr/bin/env python3
"""
Test Health Monitoring API endpoints
"""

import os
import sys
import django
from django.conf import settings
from django.test import Client
from django.contrib.auth import get_user_model
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from health.models import VitalReading, HealthAlert
from patients.models import Patient
from doctors.models import Doctor

def test_health_endpoints():
    """Test health monitoring API endpoints"""
    print("🔗 Testing Health Monitoring API endpoints...")
    
    try:
        client = Client()
        
        # Test basic endpoints without authentication first
        print("\n1. Testing basic endpoints...")
        
        # Test health check
        response = client.get('/api/health/')
        print(f"   Health check endpoint: {response.status_code}")
        
        # Test vitals endpoint (should require auth)
        response = client.get('/api/health/vitals/')
        print(f"   Vitals endpoint (no auth): {response.status_code}")
        
        # Test alerts endpoint (should require auth)
        response = client.get('/api/health/alerts/')
        print(f"   Alerts endpoint (no auth): {response.status_code}")
        
        # Test with authentication
        print("\n2. Testing with authentication...")
        
        # Get a doctor user for testing
        User = get_user_model()
        doctor_users = User.objects.filter(role='DOCTOR')[:1]
        
        if doctor_users:
            doctor_user = doctor_users[0]
            client.force_login(doctor_user)
            
            # Test vitals endpoint with auth
            response = client.get('/api/health/vitals/')
            print(f"   Vitals endpoint (with auth): {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Vitals count: {len(data) if isinstance(data, list) else 'N/A'}")
            
            # Test alerts endpoint with auth
            response = client.get('/api/health/alerts/')
            print(f"   Alerts endpoint (with auth): {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Alerts count: {len(data) if isinstance(data, list) else 'N/A'}")
            
            # Test stats endpoint
            response = client.get('/api/health/stats/')
            print(f"   Stats endpoint: {response.status_code}")
            
            # Test patient vitals endpoint
            patients = Patient.objects.all()[:1]
            if patients:
                patient = patients[0]
                response = client.get(f'/api/health/patients/{patient.id}/vitals/')
                print(f"   Patient vitals endpoint: {response.status_code}")
        else:
            print("   ⚠️  No doctor users found for authentication test")
        
        print("\n3. Testing data integrity...")
        
        # Check if we have data
        vitals_count = VitalReading.objects.count()
        alerts_count = HealthAlert.objects.count()
        patients_count = Patient.objects.count()
        doctors_count = Doctor.objects.count()
        
        print(f"   Database vitals: {vitals_count}")
        print(f"   Database alerts: {alerts_count}")
        print(f"   Database patients: {patients_count}")
        print(f"   Database doctors: {doctors_count}")
        
        print("\n✅ Health endpoints test completed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_health_endpoints()
    sys.exit(0 if success else 1)