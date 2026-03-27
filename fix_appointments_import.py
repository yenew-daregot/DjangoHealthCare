#!/usr/bin/env python
"""
Fix appointments import issue in doctors view
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_and_fix_appointments():
    """Test appointments import and fix if needed"""
    print("🔍 Testing appointments import issue...")
    
    # Test 1: Direct import
    try:
        from appointments.models import Appointment
        print("✅ Direct import successful")
        appointment_count = Appointment.objects.count()
        print(f"📊 Found {appointment_count} appointments in database")
    except Exception as e:
        print(f"❌ Direct import failed: {e}")
        return False
    
    # Test 2: Check doctors view import
    try:
        from doctors.views import HAS_APPOINTMENTS
        print(f"📊 HAS_APPOINTMENTS flag: {HAS_APPOINTMENTS}")
        
        if not HAS_APPOINTMENTS:
            print("⚠️  HAS_APPOINTMENTS is False, but direct import works!")
            print("🔧 This suggests a circular import or timing issue")
            
            # Force reload the doctors module
            import importlib
            import doctors.views
            importlib.reload(doctors.views)
            
            from doctors.views import HAS_APPOINTMENTS as RELOADED_HAS_APPOINTMENTS
            print(f"📊 After reload HAS_APPOINTMENTS: {RELOADED_HAS_APPOINTMENTS}")
            
    except Exception as e:
        print(f"❌ Doctors view import failed: {e}")
        return False
    
    # Test 3: Test the actual API endpoint
    try:
        from django.test import Client
        from django.contrib.auth import get_user_model
        from doctors.models import Doctor
        
        User = get_user_model()
        
        # Create a test doctor user if none exists
        doctor_user = User.objects.filter(role='DOCTOR').first()
        if not doctor_user:
            print("📝 Creating test doctor user...")
            doctor_user = User.objects.create_user(
                username='testdoctor',
                email='testdoctor@example.com',
                password='testpass123',
                role='DOCTOR',
                first_name='Test',
                last_name='Doctor'
            )
            
            # Create doctor profile
            doctor_profile, created = Doctor.objects.get_or_create(
                user=doctor_user,
                defaults={
                    'specialization_name': 'General Medicine',
                    'consultation_fee': 500,
                    'years_of_experience': 5
                }
            )
            print(f"✅ Created doctor profile: {doctor_profile}")
        
        # Test the API endpoint
        client = Client()
        client.force_login(doctor_user)
        
        response = client.get('/api/doctors/appointments/')
        print(f"📊 API endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API working! Response keys: {list(data.keys())}")
            return True
        else:
            print(f"❌ API error: {response.content.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def create_fix_script():
    """Create a permanent fix for the appointments import issue"""
    print("\n🔧 Creating fix for appointments import...")
    
    fix_content = '''
# Fix for appointments import in doctors/views.py
# Add this at the top of the file after other imports

import logging
logger = logging.getLogger(__name__)

# Improved appointments import with better error handling
def check_appointments_availability():
    """Check if appointments app is available and working"""
    try:
        from appointments.models import Appointment
        # Test that we can actually query the model
        Appointment.objects.count()
        return True, Appointment
    except ImportError as e:
        logger.warning(f"Appointments app not installed: {e}")
        return False, None
    except Exception as e:
        logger.error(f"Appointments app installed but not working: {e}")
        return False, None

# Use the improved check
HAS_APPOINTMENTS, Appointment = check_appointments_availability()
logger.info(f"Appointments availability: {HAS_APPOINTMENTS}")
'''
    
    print("💡 Suggested fix:")
    print(fix_content)
    
    return fix_content

if __name__ == '__main__':
    print("🚀 Starting appointments import diagnostics...\n")
    
    success = test_and_fix_appointments()
    
    if not success:
        print("\n🔧 Creating fix suggestions...")
        create_fix_script()
    else:
        print("\n✅ Appointments system is working correctly!")
        print("💡 If DoctorDashboard still shows errors, try restarting the Django server.")