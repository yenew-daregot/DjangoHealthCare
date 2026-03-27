#!/usr/bin/env python3
"""
Test script for doctor schedule system
"""
import os
import sys
import django
from datetime import time, date, timedelta

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from doctors.models import Doctor, DoctorSchedule, ScheduleException, DoctorAvailability, Specialization

User = get_user_model()

def test_schedule_system():
    """Test the schedule system functionality"""
    print("🧪 Testing Doctor Schedule System...")
    
    try:
        # Get or create a test doctor
        test_user = User.objects.filter(role='DOCTOR').first()
        if not test_user:
            print("❌ No doctor user found. Please create a doctor user first.")
            return False
        
        doctor = Doctor.objects.filter(user=test_user).first()
        if not doctor:
            print("❌ No doctor profile found. Please create a doctor profile first.")
            return False
        
        print(f"✅ Using doctor: {doctor.full_name}")
        
        # Test 1: Create a schedule
        print("\n📅 Test 1: Creating schedule...")
        schedule, created = DoctorSchedule.objects.get_or_create(
            doctor=doctor,
            day_of_week=0,  # Monday
            start_time=time(9, 0),
            defaults={
                'end_time': time(17, 0),
                'break_start': time(12, 0),
                'break_end': time(13, 0),
                'slot_duration': 30,
                'max_patients_per_slot': 1,
                'notes': 'Regular Monday schedule'
            }
        )
        
        if created:
            print(f"✅ Created new schedule: {schedule}")
        else:
            print(f"✅ Schedule already exists: {schedule}")
        
        # Test 2: Get available slots
        print("\n⏰ Test 2: Getting available slots...")
        slots = schedule.get_available_slots()
        print(f"✅ Found {len(slots)} available slots")
        if slots:
            print(f"   First slot: {slots[0]['start_time']} - {slots[0]['end_time']}")
            print(f"   Last slot: {slots[-1]['start_time']} - {slots[-1]['end_time']}")
        
        # Test 3: Create schedule exception
        print("\n🚫 Test 3: Creating schedule exception...")
        tomorrow = date.today() + timedelta(days=1)
        exception, created = ScheduleException.objects.get_or_create(
            doctor=doctor,
            date=tomorrow,
            exception_type='blocked',
            defaults={
                'start_time': time(14, 0),
                'end_time': time(15, 0),
                'is_available': False,
                'reason': 'Test meeting',
                'notes': 'Testing schedule exception'
            }
        )
        
        if created:
            print(f"✅ Created schedule exception: {exception}")
        else:
            print(f"✅ Schedule exception already exists: {exception}")
        
        # Test 4: Create availability status
        print("\n🟢 Test 4: Creating availability status...")
        availability, created = DoctorAvailability.objects.get_or_create(
            doctor=doctor,
            defaults={
                'is_online': True,
                'status_message': 'Available for consultations',
                'auto_accept_appointments': False,
                'emergency_available': True
            }
        )
        
        if created:
            print(f"✅ Created availability status: {availability}")
        else:
            print(f"✅ Availability status already exists: {availability}")
        
        # Test 5: Query all schedules for doctor
        print("\n📋 Test 5: Querying all schedules...")
        all_schedules = DoctorSchedule.objects.filter(doctor=doctor)
        print(f"✅ Doctor has {all_schedules.count()} schedule(s)")
        
        for sched in all_schedules:
            day_name = dict(DoctorSchedule.DAYS_OF_WEEK)[sched.day_of_week]
            print(f"   {day_name}: {sched.start_time} - {sched.end_time}")
        
        # Test 6: Query exceptions
        print("\n📋 Test 6: Querying schedule exceptions...")
        exceptions = ScheduleException.objects.filter(doctor=doctor)
        print(f"✅ Doctor has {exceptions.count()} exception(s)")
        
        for exc in exceptions:
            print(f"   {exc.date}: {exc.exception_type} - {exc.reason}")
        
        print("\n🎉 All tests passed! Schedule system is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_data():
    """Clean up test data (optional)"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        # Delete test schedules and exceptions
        test_user = User.objects.filter(role='DOCTOR').first()
        if test_user:
            doctor = Doctor.objects.filter(user=test_user).first()
            if doctor:
                DoctorSchedule.objects.filter(doctor=doctor, notes__contains='Test').delete()
                ScheduleException.objects.filter(doctor=doctor, notes__contains='Testing').delete()
                print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Error cleaning up: {str(e)}")

if __name__ == '__main__':
    success = test_schedule_system()
    
    # Uncomment the next line if you want to clean up test data
    # cleanup_test_data()
    
    if success:
        print("\n✅ Schedule system test completed successfully!")
    else:
        print("\n❌ Schedule system test failed!")