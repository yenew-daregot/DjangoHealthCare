#!/usr/bin/env python3
"""
Simple test to check patients API for doctors
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

User = get_user_model()

def test_patients_for_doctor():
    """Test getting patients for a specific doctor"""
    print("=== Testing Patients for Doctor ===")
    
    # Get a doctor
    doctors = User.objects.filter(role='DOCTOR')
    if doctors.count() == 0:
        print("No doctors found!")
        return
    
    doctor_user = doctors.first()
    print(f"Testing with doctor: {doctor_user.username} ({doctor_user.first_name} {doctor_user.last_name})")
    
    # Check appointments for this doctor
    try:
        appointments = Appointment.objects.filter(doctor__user=doctor_user)
        print(f"Found {appointments.count()} appointments for this doctor")
        
        if appointments.count() == 0:
            print("No appointments found. Let's create some test data...")
            
            # Get or create doctor profile
            try:
                doctor_profile = Doctor.objects.get(user=doctor_user)
            except Doctor.DoesNotExist:
                doctor_profile = Doctor.objects.create(
                    user=doctor_user,
                    specialization='General Medicine',
                    license_number=f'DOC{doctor_user.id}'
                )
                print(f"Created doctor profile for {doctor_user.username}")
            
            # Get some patients
            patients = User.objects.filter(role='PATIENT')[:3]
            if patients.count() == 0:
                print("No patients found. Creating test patients...")
                for i in range(3):
                    patient_user = User.objects.create_user(
                        username=f'testpatient{i+1}_{doctor_user.id}',
                        email=f'testpatient{i+1}_{doctor_user.id}@example.com',
                        password='testpass123',
                        first_name=f'TestPatient{i+1}',
                        last_name='ForDoctor',
                        role='PATIENT'
                    )
                    Patient.objects.create(
                        user=patient_user,
                        age=25 + i*5,
                        gender='M' if i % 2 == 0 else 'F',
                        blood_group='O+',
                        phone_number=f'123456{i}{doctor_user.id}'
                    )
                    print(f"Created patient: {patient_user.username}")
                patients = User.objects.filter(role='PATIENT')[:3]
            
            # Create appointments
            from datetime import datetime, timedelta
            for i, patient_user in enumerate(patients):
                try:
                    patient_profile = Patient.objects.get(user=patient_user)
                    appointment = Appointment.objects.create(
                        doctor=doctor_profile,
                        patient=patient_profile,
                        appointment_date=datetime.now() + timedelta(days=i),
                        reason=f'Test appointment {i+1}',
                        status='completed'
                    )
                    print(f"Created appointment: {appointment.id}")
                except Exception as e:
                    print(f"Error creating appointment: {e}")
        
        # Now test the patient filtering logic
        print("\n=== Testing Patient Filtering Logic ===")
        
        # Get patient IDs from appointments
        patient_ids = Appointment.objects.filter(doctor__user=doctor_user).values_list('patient__user_id', flat=True).distinct()
        print(f"Patient IDs from appointments: {list(patient_ids)}")
        
        # Get patients
        patients_queryset = Patient.objects.filter(user_id__in=patient_ids).select_related('user')
        print(f"Found {patients_queryset.count()} patients for doctor")
        
        for patient in patients_queryset:
            print(f"  - {patient.user.first_name} {patient.user.last_name} (ID: {patient.id}, User ID: {patient.user.id})")
        
        # Test the actual view logic
        print("\n=== Testing View Logic ===")
        from patients.views import PatientListCreateView
        
        # Create a mock request
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        mock_request = MockRequest(doctor_user)
        view = PatientListCreateView()
        view.request = mock_request
        
        queryset = view.get_queryset()
        print(f"View returned {queryset.count()} patients")
        
        for patient in queryset:
            print(f"  - {patient.user.first_name} {patient.user.last_name} (ID: {patient.id})")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_patients_for_doctor()