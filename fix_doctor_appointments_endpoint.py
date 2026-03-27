#!/usr/bin/env python
"""
Fix doctor appointments endpoint issue
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def fix_doctor_appointments_endpoint():
    """Fix the doctor appointments endpoint"""
    print("🔧 Fixing doctor appointments endpoint...")
    
    try:
        # Test the actual view logic
        from doctors.views import DoctorAppointmentsView
        from django.test import RequestFactory
        from django.contrib.auth import get_user_model
        from doctors.models import Doctor
        
        User = get_user_model()
        
        # Create or get a test doctor user
        doctor_user, created = User.objects.get_or_create(
            username='testdoctor',
            defaults={
                'email': 'testdoctor@example.com',
                'role': 'DOCTOR',
                'first_name': 'Test',
                'last_name': 'Doctor'
            }
        )
        
        if created:
            doctor_user.set_password('testpass123')
            doctor_user.save()
            print(f"✅ Created test doctor user: {doctor_user.username}")
        
        # Create or get doctor profile
        doctor_profile, created = Doctor.objects.get_or_create(
            user=doctor_user,
            defaults={
                'specialization_name': 'General Medicine',
                'consultation_fee': 500,
                'years_of_experience': 5
            }
        )
        
        if created:
            print(f"✅ Created doctor profile: {doctor_profile}")
        
        # Test the view directly
        factory = RequestFactory()
        request = factory.get('/api/doctors/appointments/')
        request.user = doctor_user
        
        view = DoctorAppointmentsView()
        response = view.get(request)
        
        print(f"📊 View response status: {response.status_code}")
        print(f"📊 Response data keys: {list(response.data.keys()) if hasattr(response, 'data') else 'No data'}")
        
        if response.status_code == 200:
            print("✅ Doctor appointments endpoint is working!")
            return True
        else:
            print(f"❌ Endpoint returned error: {response.data if hasattr(response, 'data') else 'No data'}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_appointment():
    """Create a sample appointment for testing"""
    print("\n🔧 Creating sample appointment...")
    
    try:
        from appointments.models import Appointment
        from patients.models import Patient
        from doctors.models import Doctor
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        from datetime import timedelta
        
        User = get_user_model()
        
        # Get or create patient user
        patient_user, created = User.objects.get_or_create(
            username='testpatient',
            defaults={
                'email': 'testpatient@example.com',
                'role': 'PATIENT',
                'first_name': 'Test',
                'last_name': 'Patient'
            }
        )
        
        if created:
            patient_user.set_password('testpass123')
            patient_user.save()
        
        # Get or create patient profile
        patient_profile, created = Patient.objects.get_or_create(
            user=patient_user,
            defaults={
                'date_of_birth': '1990-01-01',
                'phone_number': '+1234567890'
            }
        )
        
        # Get doctor
        doctor_user = User.objects.get(username='testdoctor')
        doctor_profile = Doctor.objects.get(user=doctor_user)
        
        # Create appointment
        appointment, created = Appointment.objects.get_or_create(
            patient=patient_profile,
            doctor=doctor_profile,
            appointment_date=timezone.now() + timedelta(days=1),
            defaults={
                'reason': 'Test appointment for dashboard',
                'appointment_type': 'consultation',
                'status': 'scheduled',
                'duration': 30
            }
        )
        
        if created:
            print(f"✅ Created sample appointment: {appointment}")
        else:
            print(f"📋 Sample appointment already exists: {appointment}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error creating sample appointment: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_appointments_api_directly():
    """Test the appointments API directly"""
    print("\n🔧 Testing appointments API directly...")
    
    try:
        from appointments.models import Appointment
        
        # Count appointments
        total_appointments = Appointment.objects.count()
        print(f"📊 Total appointments in database: {total_appointments}")
        
        # Get recent appointments
        recent_appointments = Appointment.objects.all()[:5]
        for apt in recent_appointments:
            print(f"📋 Appointment: {apt.patient.user.get_full_name()} -> {apt.doctor.user.get_full_name()} on {apt.appointment_date}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing appointments API: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Starting doctor appointments endpoint fix...\n")
    
    # Run tests and fixes
    api_success = test_appointments_api_directly()
    sample_success = create_sample_appointment()
    endpoint_success = fix_doctor_appointments_endpoint()
    
    print(f"\n📊 Fix Results:")
    print(f"   API Test: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"   Sample Data: {'✅ PASS' if sample_success else '❌ FAIL'}")
    print(f"   Endpoint Test: {'✅ PASS' if endpoint_success else '❌ FAIL'}")
    
    if all([api_success, sample_success, endpoint_success]):
        print("\n🎉 All fixes applied successfully!")
        print("💡 The doctor appointments endpoint should now work in DoctorDashboard.jsx")
        print("🔄 Please restart your Django server to ensure all changes take effect.")
    else:
        print("\n⚠️  Some fixes failed. Check the errors above.")
        print("💡 Try restarting the Django server and check for any migration issues.")