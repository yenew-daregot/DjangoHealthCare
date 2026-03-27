#!/usr/bin/env python3
"""
Debug script to check patients API for doctors
"""
import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from patients.models import Patient
from appointments.models import Appointment
from doctors.models import Doctor
from patients.views import PatientListCreateView

User = get_user_model()

def debug_patients_api():
    """Debug the patients API for doctors"""
    print("=== Debugging Patients API ===")
    
    # Get a doctor
    doctors = User.objects.filter(role='DOCTOR')
    if doctors.count() == 0:
        print("No doctors found!")
        return
    
    doctor_user = doctors.first()
    print(f"Testing with doctor: {doctor_user.username} ({doctor_user.first_name} {doctor_user.last_name})")
    
    # Check if doctor has a profile
    try:
        doctor_profile = Doctor.objects.get(user=doctor_user)
        print(f"Doctor profile found: {doctor_profile}")
    except Doctor.DoesNotExist:
        print("Doctor profile not found!")
        return
    
    # Check appointments for this doctor
    appointments = Appointment.objects.filter(doctor__user=doctor_user)
    print(f"Found {appointments.count()} appointments for this doctor")
    
    if appointments.count() > 0:
        print("Appointments:")
        for apt in appointments[:5]:  # Show first 5
            print(f"  - {apt.id}: {apt.patient.user.first_name} {apt.patient.user.last_name} ({apt.status})")
    
    # Test the view logic directly
    print("\n=== Testing View Logic ===")
    
    class MockRequest:
        def __init__(self, user):
            self.user = user
    
    mock_request = MockRequest(doctor_user)
    view = PatientListCreateView()
    view.request = mock_request
    
    try:
        queryset = view.get_queryset()
        print(f"View returned {queryset.count()} patients")
        
        for patient in queryset:
            print(f"  - {patient.user.first_name} {patient.user.last_name} (ID: {patient.id})")
            
        # Test serialization
        from patients.serializers import PatientSerializer
        serializer = PatientSerializer(queryset, many=True)
        serialized_data = serializer.data
        print(f"\nSerialized data: {len(serialized_data)} patients")
        for patient_data in serialized_data:
            user_info = patient_data.get('user', {})
            print(f"  - {user_info.get('first_name')} {user_info.get('last_name')} (ID: {patient_data.get('id')})")
            
    except Exception as e:
        print(f"Error in view logic: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_patients_api()