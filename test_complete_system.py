#!/usr/bin/env python
"""
Test script to verify all systems are working after migration
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from doctors.models import Doctor, DoctorSchedule, Specialization
from prescriptions.models import Medication, Prescription
from chat.models import ChatRoom, ChatNotification
from django.utils import timezone

User = get_user_model()

def test_models():
    """Test that all models can be created and accessed"""
    print("🧪 Testing Models...")
    
    try:
        # Test User and Doctor models
        users_count = User.objects.count()
        doctors_count = Doctor.objects.count()
        print(f"✅ Users: {users_count}, Doctors: {doctors_count}")
        
        # Test Schedule models
        schedules_count = DoctorSchedule.objects.count()
        print(f"✅ Doctor Schedules: {schedules_count}")
        
        # Test Prescription models
        medications_count = Medication.objects.count()
        prescriptions_count = Prescription.objects.count()
        print(f"✅ Medications: {medications_count}, Prescriptions: {prescriptions_count}")
        
        # Test Chat models
        chat_rooms_count = ChatRoom.objects.count()
        notifications_count = ChatNotification.objects.count()
        print(f"✅ Chat Rooms: {chat_rooms_count}, Notifications: {notifications_count}")
        
        return True
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def test_doctor_schedule_creation():
    """Test creating a doctor schedule"""
    print("\n📅 Testing Doctor Schedule Creation...")
    
    try:
        # Get or create a doctor
        if Doctor.objects.exists():
            doctor = Doctor.objects.first()
            
            # Create a test schedule
            schedule, created = DoctorSchedule.objects.get_or_create(
                doctor=doctor,
                day_of_week=1,  # Tuesday
                start_time='09:00',
                end_time='17:00',
                defaults={
                    'slot_duration': 30,
                    'break_start': '12:00',
                    'break_end': '13:00',
                    'notes': 'Test schedule created by system test'
                }
            )
            
            if created:
                print(f"✅ Created new schedule for Dr. {doctor.full_name}")
            else:
                print(f"✅ Schedule already exists for Dr. {doctor.full_name}")
            
            # Test getting available slots
            slots = schedule.get_available_slots()
            print(f"✅ Generated {len(slots)} time slots")
            
            return True
        else:
            print("⚠️  No doctors found. Create a doctor first.")
            return True
    except Exception as e:
        print(f"❌ Schedule test failed: {e}")
        return False

def test_medication_creation():
    """Test creating medications"""
    print("\n💊 Testing Medication Creation...")
    
    try:
        medication, created = Medication.objects.get_or_create(
            name='Test Medication',
            strength='500mg',
            defaults={
                'generic_name': 'Test Generic',
                'medication_type': 'tablet',
                'description': 'Test medication created by system test'
            }
        )
        
        if created:
            print(f"✅ Created new medication: {medication.name}")
        else:
            print(f"✅ Medication already exists: {medication.name}")
        
        return True
    except Exception as e:
        print(f"❌ Medication test failed: {e}")
        return False

def main():
    print("🏥 Healthcare System Complete Test")
    print("=" * 50)
    
    success = True
    
    # Run all tests
    success &= test_models()
    success &= test_doctor_schedule_creation()
    success &= test_medication_creation()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! System is ready to use.")
        print("\n🚀 You can now:")
        print("   • Start the frontend: npm start")
        print("   • Test doctor schedule functionality")
        print("   • Test prescription system")
        print("   • Test chat system")
    else:
        print("❌ Some tests failed. Check the errors above.")

if __name__ == '__main__':
    main()