#!/usr/bin/env python3
"""
Create test appointments to link doctors with patients
"""
import os
import sys
import django
from datetime import datetime, timedelta

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

def create_test_appointments():
    """Create test appointments linking doctors with patients"""
    print("=== Creating Test Appointments ===")
    
    # Get doctors and patients
    doctors = User.objects.filter(role='DOCTOR')
    patients = User.objects.filter(role='PATIENT')
    
    print(f"Found {doctors.count()} doctors and {patients.count()} patients")
    
    if doctors.count() == 0 or patients.count() == 0:
        print("Need both doctors and patients to create appointments")
        return
    
    appointments_created = 0
    
    # For each doctor, create appointments with a few patients
    for doctor_user in doctors[:5]:  # Limit to first 5 doctors
        print(f"\nProcessing doctor: {doctor_user.username}")
        
        # Get or create doctor profile
        try:
            doctor_profile = Doctor.objects.get(user=doctor_user)
        except Doctor.DoesNotExist:
            doctor_profile = Doctor.objects.create(
                user=doctor_user,
                specialization='General Medicine',
                license_number=f'DOC{doctor_user.id}',
                years_of_experience=5
            )
            print(f"  Created doctor profile for {doctor_user.username}")
        
        # Create appointments with 3-5 patients
        patient_users = patients[:5]  # Take first 5 patients
        
        for i, patient_user in enumerate(patient_users):
            try:
                # Get or create patient profile
                try:
                    patient_profile = Patient.objects.get(user=patient_user)
                except Patient.DoesNotExist:
                    patient_profile = Patient.objects.create(
                        user=patient_user,
                        age=25 + (i * 5),
                        gender='male' if i % 2 == 0 else 'female',
                        blood_group='O+'
                    )
                    print(f"  Created patient profile for {patient_user.username}")
                
                # Check if appointment already exists
                existing = Appointment.objects.filter(
                    doctor=doctor_profile,
                    patient=patient_profile
                ).exists()
                
                if not existing:
                    appointment = Appointment.objects.create(
                        doctor=doctor_profile,
                        patient=patient_profile,
                        appointment_date=datetime.now() + timedelta(days=i),
                        reason=f'Consultation {i+1}',
                        status='completed',
                        appointment_type='consultation'
                    )
                    appointments_created += 1
                    print(f"  Created appointment: {appointment.appointment_number}")
                else:
                    print(f"  Appointment already exists between {doctor_user.username} and {patient_user.username}")
                    
            except Exception as e:
                print(f"  Error creating appointment with {patient_user.username}: {e}")
    
    print(f"\n=== Summary ===")
    print(f"Created {appointments_created} new appointments")
    print(f"Total appointments in system: {Appointment.objects.count()}")
    
    # Test the patients API for a doctor
    print(f"\n=== Testing Patients API ===")
    test_doctor = doctors.first()
    print(f"Testing with doctor: {test_doctor.username}")
    
    # Get patient IDs from appointments
    patient_ids = Appointment.objects.filter(doctor__user=test_doctor).values_list('patient_id', flat=True).distinct()
    patients_for_doctor = Patient.objects.filter(id__in=patient_ids).select_related('user')
    
    print(f"Found {patients_for_doctor.count()} patients for doctor {test_doctor.username}:")
    for patient in patients_for_doctor:
        print(f"  - {patient.user.first_name} {patient.user.last_name} (ID: {patient.id})")

if __name__ == '__main__':
    create_test_appointments()