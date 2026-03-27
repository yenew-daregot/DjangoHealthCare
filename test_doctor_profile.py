#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from doctors.models import Doctor
from doctors.views import DoctorProfileView
from users.models import User

def test_doctor_profile():
    print("Testing doctor profile endpoint...")
    
    try:
        # Check if we have doctors
        doctors = Doctor.objects.all()
        print(f"Total doctors: {doctors.count()}")
        
        if doctors.count() == 0:
            print("❌ No doctors found")
            return
            
        # Get first doctor
        doctor = doctors.first()
        print(f"Testing with doctor: {doctor.user.username} (ID: {doctor.id})")
        
        # Create test request
        factory = RequestFactory()
        request = factory.get('/api/doctors/profile/')
        request.user = doctor.user
        
        # Test the view
        view = DoctorProfileView()
        view.setup(request)
        
        try:
            response = view.get(request)
            print(f"✅ Profile endpoint works! Status: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Profile data keys: {list(response.data.keys()) if response.data else 'No data'}")
        except Exception as e:
            print(f"❌ Profile endpoint error: {e}")
            
        # Also test direct model access
        print(f"Doctor profile fields:")
        print(f"  - User: {doctor.user.first_name} {doctor.user.last_name}")
        print(f"  - Specialization: {doctor.specialization}")
        print(f"  - Available: {doctor.is_available}")
        print(f"  - Verified: {doctor.is_verified}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_doctor_profile()