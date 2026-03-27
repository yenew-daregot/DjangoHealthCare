#!/usr/bin/env python3
"""
Check patient data in detail
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

User = get_user_model()

def check_patient_data():
    """Check patient data in detail"""
    print("=== Checking Patient Data ===")
    
    # Get a doctor
    doctor_user = User.objects.filter(role='DOCTOR').first()
    print(f"Doctor: {doctor_user.username}")
    
    # Get appointments for this doctor
    appointments = Appointment.objects.filter(doctor__user=doctor_user)
    patient_ids = appointments.values_list('patient_id', flat=True).distinct()
    patients = Patient.objects.filter(id__in=patient_ids).select_related('user')
    
    print(f"Found {patients.count()} patients:")
    
    for patient in patients:
        print(f"\nPatient ID: {patient.id}")
        print(f"  User ID: {patient.user.id}")
        print(f"  Username: {patient.user.username}")
        print(f"  First Name: '{patient.user.first_name}'")
        print(f"  Last Name: '{patient.user.last_name}'")
        print(f"  Email: {patient.user.email}")
        print(f"  Role: {patient.user.role}")
        print(f"  Age: {patient.age}")
        print(f"  Gender: {patient.gender}")
        print(f"  Blood Group: {patient.blood_group}")
        
        # Check if names are empty and try to fix
        if not patient.user.first_name and not patient.user.last_name:
            print(f"  ⚠️ Names are empty! Fixing...")
            patient.user.first_name = f"Patient{patient.id}"
            patient.user.last_name = "User"
            # Fix phone number if invalid
            if not patient.user.phone_number or len(patient.user.phone_number) < 10:
                patient.user.phone_number = f"123456789{patient.id % 10}"
            patient.user.save()
            print(f"  ✅ Updated to: {patient.user.first_name} {patient.user.last_name}")

if __name__ == '__main__':
    check_patient_data()