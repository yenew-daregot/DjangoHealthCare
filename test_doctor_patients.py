#!/usr/bin/env python3
"""
Test script to check doctor's patients API
"""
import os
import sys
import django
import requests
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

def test_doctor_patients_api():
    """Test the doctor's patients API endpoint"""
    print("=== Testing Doctor's Patients API ===")
    
    # Check if we have any doctors
    doctors = User.objects.filter(role='DOCTOR')
    print(f"Found {doctors.count()} doctors in the system")
    
    if doctors.count() == 0:
        print("No doctors found. Creating a test doctor...")
        # Create a test doctor
        doctor_user = User.objects.create_user(
            username='testdoctor',
            email='testdoctor@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Doctor',
            role='DOCTOR'
        )
        Doctor.objects.create(
            user=doctor_user,
            specialization='General Medicine',
            license_number='DOC123456'
        )
        print(f"Created test doctor: {doctor_user.username}")
    else:
        doctor_user = doctors.first()
        print(f"Using existing doctor: {doctor_user.username}")
    
    # Check if we have any patients
    patients = User.objects.filter(role='PATIENT')
    print(f"Found {patients.count()} patients in the system")
    
    if patients.count() == 0:
        print("No patients found. Creating test patients...")
        # Create test patients
        for i in range(3):
            patient_user = User.objects.create_user(
                username=f'testpatient{i+1}',
                email=f'testpatient{i+1}@example.com',
                password='testpass123',
                first_name=f'Test{i+1}',
                last_name='Patient',
                role='PATIENT'
            )
            Patient.objects.create(
                user=patient_user,
                age=25 + i*10,
                gender='M' if i % 2 == 0 else 'F',
                blood_group='O+',
                phone_number=f'123456789{i}'
            )
            print(f"Created test patient: {patient_user.username}")
    
    # Get patients for appointments
    patient_users = User.objects.filter(role='PATIENT')[:2]
    
    # Check if we have appointments between doctor and patients
    appointments = Appointment.objects.filter(doctor=doctor_user)
    print(f"Found {appointments.count()} appointments for doctor {doctor_user.username}")
    
    if appointments.count() == 0:
        print("No appointments found. Creating test appointments...")
        # Create test appointments
        for i, patient_user in enumerate(patient_users):
            appointment = Appointment.objects.create(
                doctor=doctor_user,
                patient=patient_user,
                appointment_date=(datetime.now() + timedelta(days=i)).date(),
                appointment_time='10:00:00',
                reason=f'Test appointment {i+1}',
                status='completed'
            )
            print(f"Created appointment: {appointment.id} between {doctor_user.username} and {patient_user.username}")
    
    # Now test the API
    print("\n=== Testing API Endpoints ===")
    
    # Test login to get token
    login_data = {
        'username': doctor_user.username,
        'password': 'testpass123'
    }
    
    try:
        login_response = requests.post('http://localhost:8000/api/auth/login/', json=login_data)
        if login_response.status_code == 200:
            token = login_response.json().get('access')
            print(f"✓ Login successful, got token")
            
            # Test patients API
            headers = {'Authorization': f'Bearer {token}'}
            patients_response = requests.get('http://localhost:8000/api/patients/', headers=headers)
            
            if patients_response.status_code == 200:
                patients_data = patients_response.json()
                print(f"✓ Patients API successful")
                print(f"  Response type: {type(patients_data)}")
                
                if isinstance(patients_data, dict) and 'results' in patients_data:
                    patients_list = patients_data['results']
                    print(f"  Found {len(patients_list)} patients for doctor")
                elif isinstance(patients_data, list):
                    patients_list = patients_data
                    print(f"  Found {len(patients_list)} patients for doctor")
                else:
                    patients_list = []
                    print(f"  Unexpected response format: {patients_data}")
                
                # Print patient details
                for patient in patients_list:
                    user_info = patient.get('user', {})
                    print(f"  - Patient: {user_info.get('first_name')} {user_info.get('last_name')} (ID: {patient.get('id')})")
                
            else:
                print(f"✗ Patients API failed: {patients_response.status_code}")
                print(f"  Response: {patients_response.text}")
        else:
            print(f"✗ Login failed: {login_response.status_code}")
            print(f"  Response: {login_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server. Make sure the backend is running on localhost:8000")
    except Exception as e:
        print(f"✗ Error testing API: {e}")

def check_database_state():
    """Check the current state of the database"""
    print("\n=== Database State ===")
    
    users = User.objects.all()
    doctors = User.objects.filter(role='DOCTOR')
    patients = User.objects.filter(role='PATIENT')
    appointments = Appointment.objects.all()
    
    print(f"Total users: {users.count()}")
    print(f"Doctors: {doctors.count()}")
    print(f"Patients: {patients.count()}")
    print(f"Appointments: {appointments.count()}")
    
    print("\nDoctors:")
    for doctor in doctors:
        print(f"  - {doctor.username} ({doctor.first_name} {doctor.last_name})")
    
    print("\nPatients:")
    for patient in patients:
        print(f"  - {patient.username} ({patient.first_name} {patient.last_name})")
    
    print("\nAppointments:")
    for appointment in appointments:
        print(f"  - {appointment.id}: Dr. {appointment.doctor.user.username} -> {appointment.patient.user.username} ({appointment.status})")

if __name__ == '__main__':
    check_database_state()
    test_doctor_patients_api()