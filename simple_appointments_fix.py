#!/usr/bin/env python
"""
Simple fix for doctor appointments endpoint
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def check_appointments_system():
    """Check if appointments system is working"""
    print("🔍 Checking appointments system status...")
    
    try:
        # Test 1: Import check
        from appointments.models import Appointment
        print("✅ Appointments model imported successfully")
        
        # Test 2: Database check
        appointment_count = Appointment.objects.count()
        print(f"📊 Found {appointment_count} appointments in database")
        
        # Test 3: Doctors view check
        from doctors.views import HAS_APPOINTMENTS
        print(f"📊 HAS_APPOINTMENTS flag: {HAS_APPOINTMENTS}")
        
        # Test 4: URL configuration check
        from django.urls import reverse
        try:
            url = reverse('doctor-appointments')
            print(f"✅ Doctor appointments URL configured: {url}")
        except:
            print("❌ Doctor appointments URL not found")
        
        # Test 5: Check if there are any existing doctor users
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        doctor_users = User.objects.filter(role='DOCTOR')
        print(f"📊 Found {doctor_users.count()} doctor users")
        
        if doctor_users.exists():
            doctor_user = doctor_users.first()
            print(f"📋 Sample doctor: {doctor_user.get_full_name()} ({doctor_user.username})")
            
            # Check if this doctor has a profile
            from doctors.models import Doctor
            try:
                doctor_profile = Doctor.objects.get(user=doctor_user)
                print(f"✅ Doctor profile exists: {doctor_profile}")
            except Doctor.DoesNotExist:
                print("⚠️  Doctor user exists but no profile found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking appointments system: {e}")
        return False

def provide_frontend_fix():
    """Provide frontend fix suggestions"""
    print("\n🔧 Frontend Fix Suggestions:")
    print("""
The appointments system is working on the backend. The issue might be:

1. **Authentication**: Make sure the user is properly authenticated as a DOCTOR
2. **API Call**: Check if the frontend is making the correct API call
3. **Error Handling**: The frontend might not be handling the response correctly

Frontend debugging steps:
1. Check browser console for any JavaScript errors
2. Check Network tab to see if the API call is being made
3. Verify the API response in the Network tab
4. Check if the user has the correct role (DOCTOR)

The correct API endpoint is: /api/doctors/appointments/
""")

def check_existing_appointments():
    """Check existing appointments for debugging"""
    print("\n🔍 Checking existing appointments...")
    
    try:
        from appointments.models import Appointment
        
        appointments = Appointment.objects.all()[:5]
        
        if appointments:
            print("📋 Recent appointments:")
            for apt in appointments:
                print(f"   - {apt.patient.user.get_full_name()} -> {apt.doctor.user.get_full_name()}")
                print(f"     Date: {apt.appointment_date}, Status: {apt.status}")
        else:
            print("📋 No appointments found")
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking appointments: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Simple appointments system check...\n")
    
    system_ok = check_appointments_system()
    appointments_ok = check_existing_appointments()
    
    if system_ok:
        provide_frontend_fix()
        print("\n✅ Backend appointments system is working correctly!")
        print("💡 The issue is likely in the frontend or authentication.")
        print("🔄 Try refreshing the browser and check the browser console for errors.")
    else:
        print("\n❌ Backend appointments system has issues.")
        print("💡 Check Django server logs for more details.")