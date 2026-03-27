#!/usr/bin/env python
"""
Test the doctor appointments endpoint directly
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_doctor_appointments_endpoint():
    """Test the doctor appointments endpoint with a real doctor user"""
    print("🔍 Testing doctor appointments endpoint...")
    
    try:
        from django.contrib.auth import get_user_model
        from doctors.models import Doctor
        from doctors.views import DoctorAppointmentsView
        from django.test import RequestFactory
        import json
        
        User = get_user_model()
        
        # Get an existing doctor user
        doctor_users = User.objects.filter(role='DOCTOR')
        if not doctor_users.exists():
            print("❌ No doctor users found")
            return False
        
        doctor_user = doctor_users.first()
        print(f"📋 Testing with doctor: {doctor_user.get_full_name()} ({doctor_user.username})")
        
        # Check if doctor has profile
        try:
            doctor_profile = Doctor.objects.get(user=doctor_user)
            print(f"✅ Doctor profile found: {doctor_profile}")
        except Doctor.DoesNotExist:
            print("❌ Doctor profile not found")
            return False
        
        # Create request
        factory = RequestFactory()
        request = factory.get('/api/doctors/appointments/')
        request.user = doctor_user
        
        # Test the view
        view = DoctorAppointmentsView()
        response = view.get(request)
        
        print(f"📊 Response status: {response.status_code}")
        
        if hasattr(response, 'data'):
            print(f"📊 Response data keys: {list(response.data.keys())}")
            
            if 'results' in response.data:
                print(f"📊 Number of appointments: {len(response.data['results'])}")
                print(f"📊 Total count: {response.data.get('count', 'N/A')}")
                
                # Show first appointment if any
                if response.data['results']:
                    first_apt = response.data['results'][0]
                    print(f"📋 First appointment: {first_apt.get('patient', {}).get('name', 'N/A')} - {first_apt.get('status', 'N/A')}")
            
            if 'error' in response.data:
                print(f"❌ Error in response: {response.data['error']}")
                if 'detail' in response.data:
                    print(f"❌ Error detail: {response.data['detail']}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_appointment_model_structure():
    """Check the appointment model structure"""
    print("\n🔍 Checking appointment model structure...")
    
    try:
        from appointments.models import Appointment
        
        # Get model fields
        fields = [f.name for f in Appointment._meta.get_fields()]
        print(f"📊 Appointment model fields: {fields}")
        
        # Check for doctor relationship
        doctor_fields = [f for f in fields if 'doctor' in f.lower()]
        print(f"📊 Doctor-related fields: {doctor_fields}")
        
        # Check if there are any appointments
        total_appointments = Appointment.objects.count()
        print(f"📊 Total appointments: {total_appointments}")
        
        if total_appointments > 0:
            # Get a sample appointment
            sample_apt = Appointment.objects.first()
            print(f"📋 Sample appointment:")
            print(f"   - ID: {sample_apt.id}")
            print(f"   - Patient: {sample_apt.patient}")
            print(f"   - Doctor: {sample_apt.doctor}")
            print(f"   - Status: {sample_apt.status}")
            print(f"   - Date: {getattr(sample_apt, 'appointment_date', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking model: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Testing doctor appointments endpoint...\n")
    
    model_ok = check_appointment_model_structure()
    endpoint_ok = test_doctor_appointments_endpoint()
    
    print(f"\n📊 Test Results:")
    print(f"   Model Check: {'✅ PASS' if model_ok else '❌ FAIL'}")
    print(f"   Endpoint Test: {'✅ PASS' if endpoint_ok else '❌ FAIL'}")
    
    if model_ok and endpoint_ok:
        print("\n✅ Doctor appointments endpoint is working!")
        print("💡 The issue might be in the frontend authentication or error handling.")
    else:
        print("\n❌ There are issues with the appointments system.")
        print("💡 Check the errors above for more details.")