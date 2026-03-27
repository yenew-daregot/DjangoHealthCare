#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from doctors.models import Doctor
from patients.models import Patient
from chat.models import ChatRoom, Message, ChatParticipant
from chat.views import DoctorChatRoomsView, ChatTestView
import json

User = get_user_model()

def test_chat_diagnosis():
    print("=== COMPREHENSIVE CHAT SYSTEM DIAGNOSIS ===\n")
    
    # 1. Check database state
    print("1. DATABASE STATE:")
    print(f"   Users: {User.objects.count()}")
    print(f"   Doctors: {Doctor.objects.count()}")
    print(f"   Patients: {Patient.objects.count()}")
    print(f"   Chat Rooms: {ChatRoom.objects.count()}")
    print(f"   Messages: {Message.objects.count()}")
    print(f"   Participants: {ChatParticipant.objects.count()}")
    
    # 2. Check doctor users
    print("\n2. DOCTOR USERS:")
    doctor_users = User.objects.filter(user_type='DOCTOR')
    print(f"   Doctor users found: {doctor_users.count()}")
    
    if doctor_users.exists():
        doctor_user = doctor_users.first()
        print(f"   Sample doctor user: {doctor_user.username} ({doctor_user.first_name} {doctor_user.last_name})")
        
        # Check if doctor profile exists
        try:
            doctor_profile = Doctor.objects.get(user=doctor_user)
            print(f"   Doctor profile: ID {doctor_profile.id}, Available: {doctor_profile.is_available}")
            
            # 3. Test doctor profile endpoint
            print("\n3. TESTING DOCTOR PROFILE ENDPOINT:")
            client = Client()
            
            # Login as doctor
            login_response = client.post('/api/auth/login/', {
                'username': doctor_user.username,
                'password': 'password123'  # Default password from create_missing_doctor_profiles.py
            })
            
            if login_response.status_code == 200:
                print("   ✅ Doctor login successful")
                
                # Get profile
                profile_response = client.get('/api/doctors/profile/')
                print(f"   Profile endpoint status: {profile_response.status_code}")
                
                if profile_response.status_code == 200:
                    print("   ✅ Doctor profile endpoint working")
                    profile_data = profile_response.json()
                    print(f"   Profile data keys: {list(profile_data.keys())}")
                else:
                    print(f"   ❌ Doctor profile endpoint failed: {profile_response.content}")
                
                # 4. Test chat endpoints
                print("\n4. TESTING CHAT ENDPOINTS:")
                
                # Test chat root
                chat_root_response = client.get('/api/chat/')
                print(f"   Chat root status: {chat_root_response.status_code}")
                
                # Test chat test endpoint
                chat_test_response = client.get('/api/chat/test/')
                print(f"   Chat test status: {chat_test_response.status_code}")
                if chat_test_response.status_code == 200:
                    test_data = chat_test_response.json()
                    print(f"   Chat test data: {json.dumps(test_data, indent=2)}")
                
                # Test doctor chat rooms
                doctor_chat_response = client.get(f'/api/chat/rooms/doctor/{doctor_profile.id}/')
                print(f"   Doctor chat rooms status: {doctor_chat_response.status_code}")
                if doctor_chat_response.status_code == 200:
                    chat_data = doctor_chat_response.json()
                    print(f"   Chat rooms count: {len(chat_data) if isinstance(chat_data, list) else 'Not a list'}")
                else:
                    print(f"   Doctor chat rooms error: {doctor_chat_response.content}")
                
            else:
                print(f"   ❌ Doctor login failed: {login_response.content}")
                
        except Doctor.DoesNotExist:
            print("   ❌ Doctor profile not found for user")
    else:
        print("   ❌ No doctor users found")
    
    # 5. Create test data if needed
    print("\n5. CREATING TEST DATA:")
    
    # Create a patient if none exists
    if Patient.objects.count() == 0:
        print("   Creating test patient...")
        try:
            patient_user = User.objects.create_user(
                username='testpatient',
                email='patient@test.com',
                password='password123',
                first_name='Test',
                last_name='Patient',
                user_type='PATIENT'
            )
            patient = Patient.objects.create(
                user=patient_user,
                date_of_birth='1990-01-01',
                phone='1234567890'
            )
            print(f"   ✅ Test patient created: {patient.id}")
        except Exception as e:
            print(f"   ❌ Failed to create test patient: {e}")
    
    # Create a test chat room if none exists
    if ChatRoom.objects.count() == 0 and Doctor.objects.exists() and Patient.objects.exists():
        print("   Creating test chat room...")
        try:
            doctor = Doctor.objects.first()
            patient = Patient.objects.first()
            
            chat_room = ChatRoom.objects.create(
                patient=patient,
                doctor=doctor,
                room_type='consultation',
                title=f'Test chat between {patient.user.first_name} and Dr. {doctor.user.first_name}'
            )
            
            # Create participants
            ChatParticipant.objects.create(
                chat_room=chat_room,
                user=patient.user,
                role='patient'
            )
            ChatParticipant.objects.create(
                chat_room=chat_room,
                user=doctor.user,
                role='doctor'
            )
            
            # Create a test message
            Message.objects.create(
                chat_room=chat_room,
                sender=patient.user,
                content='Hello Doctor, I need help with my condition.',
                message_type='text'
            )
            
            print(f"   ✅ Test chat room created: {chat_room.id}")
            
        except Exception as e:
            print(f"   ❌ Failed to create test chat room: {e}")
    
    print("\n=== DIAGNOSIS COMPLETE ===")
    print("If you're still seeing 'Please try again', check:")
    print("1. Make sure you're logged in as a doctor user")
    print("2. Ensure the doctor has a complete profile")
    print("3. Check browser console for detailed error messages")
    print("4. Verify the backend server is running on the correct port")

if __name__ == '__main__':
    test_chat_diagnosis()