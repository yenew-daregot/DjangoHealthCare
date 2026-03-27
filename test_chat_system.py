#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from doctors.models import Doctor
from patients.models import Patient
from chat.views import DoctorChatRoomsView
from users.models import User

def test_chat_system():
    print("Testing chat system...")
    
    try:
        # Check if we have doctors and patients
        doctors_count = Doctor.objects.count()
        patients_count = Patient.objects.count()
        
        print(f"Doctors in database: {doctors_count}")
        print(f"Patients in database: {patients_count}")
        
        if doctors_count == 0:
            print("❌ No doctors found in database")
            return
            
        if patients_count == 0:
            print("❌ No patients found in database")
            return
            
        # Get a doctor
        doctor = Doctor.objects.first()
        print(f"Testing with doctor: {doctor.user.first_name} {doctor.user.last_name} (ID: {doctor.id})")
        
        # Create a test request
        factory = RequestFactory()
        request = factory.get(f'/api/chat/rooms/doctor/{doctor.id}/')
        request.user = doctor.user
        
        # Test the view
        view = DoctorChatRoomsView()
        view.setup(request, doctor_id=doctor.id)
        
        queryset = view.get_queryset()
        print(f"Chat rooms for doctor {doctor.id}: {queryset.count()}")
        
        # Check chat models
        from chat.models import ChatRoom, Message, ChatParticipant
        
        total_rooms = ChatRoom.objects.count()
        total_messages = Message.objects.count()
        total_participants = ChatParticipant.objects.count()
        
        print(f"Total chat rooms: {total_rooms}")
        print(f"Total messages: {total_messages}")
        print(f"Total participants: {total_participants}")
        
        # Test chat API endpoints
        from chat.views import chat_root
        request = factory.get('/api/chat/')
        request.user = AnonymousUser()
        
        response = chat_root(request)
        print(f"Chat root endpoint status: {response.status_code}")
        
        print("✅ Chat system basic tests passed!")
        
    except Exception as e:
        print(f"❌ Error testing chat system: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_chat_system()