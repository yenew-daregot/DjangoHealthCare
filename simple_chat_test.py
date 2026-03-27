#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from doctors.models import Doctor
from patients.models import Patient
from chat.models import ChatRoom, Message, ChatParticipant

User = get_user_model()

def simple_chat_test():
    print("=== SIMPLE CHAT TEST ===")
    
    # Check basic counts
    print(f"Users: {User.objects.count()}")
    print(f"Doctors: {Doctor.objects.count()}")
    print(f"Patients: {Patient.objects.count()}")
    print(f"Chat Rooms: {ChatRoom.objects.count()}")
    
    # Check doctor users
    doctor_users = User.objects.filter(user_type='DOCTOR')
    print(f"Doctor users: {doctor_users.count()}")
    
    if doctor_users.exists():
        doctor_user = doctor_users.first()
        print(f"Sample doctor: {doctor_user.username}")
        
        try:
            doctor_profile = Doctor.objects.get(user=doctor_user)
            print(f"Doctor profile exists: {doctor_profile.id}")
            print("✅ Basic setup looks good")
        except Doctor.DoesNotExist:
            print("❌ Doctor profile missing")
    else:
        print("❌ No doctor users found")
    
    # Create minimal test data if needed
    if ChatRoom.objects.count() == 0 and Doctor.objects.exists() and Patient.objects.exists():
        print("Creating test chat room...")
        doctor = Doctor.objects.first()
        patient = Patient.objects.first()
        
        chat_room = ChatRoom.objects.create(
            patient=patient,
            doctor=doctor,
            room_type='consultation'
        )
        print(f"✅ Test chat room created: {chat_room.id}")

if __name__ == '__main__':
    simple_chat_test()