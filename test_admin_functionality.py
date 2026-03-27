#!/usr/bin/env python3
"""
Test script to verify admin functionality fixes
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/workspaces/healthcare-management-system/backend')
django.setup()

from django.contrib.auth import get_user_model
from doctors.models import Doctor, Specialization
from patients.models import Patient
from admin_dashboard.serializers import AdminCreatePatientSerializer, AdminCreateDoctorSerializer

User = get_user_model()

def test_specializations():
    """Test that specializations exist and can be fetched"""
    print("=" * 50)
    print("TESTING SPECIALIZATIONS")
    print("=" * 50)
    
    # Check if specializations exist
    specializations = Specialization.objects.all()
    print(f"Total specializations: {specializations.count()}")
    
    if specializations.count() == 0:
        print("Creating default specializations...")
        default_specs = [
            'General Medicine',
            'Cardiology', 
            'Dermatology',
            'Neurology',
            'Orthopedics',
            'Pediatrics',
            'Psychiatry',
            'Surgery'
        ]
        
        for spec_name in default_specs:
            spec, created = Specialization.objects.get_or_create(
                name=spec_name,
                defaults={'description': f'Specialization in {spec_name}'}
            )
            if created:
                print(f"✅ Created specialization: {spec_name}")
            else:
                print(f"⚠️  Specialization already exists: {spec_name}")
    
    # List all specializations
    print("\nAvailable specializations:")
    for spec in Specialization.objects.all():
        print(f"  - ID: {spec.id}, Name: {spec.name}")
    
    return True

def test_patient_data_structure():
    """Test patient data structure for name display"""
    print("=" * 50)
    print("TESTING PATIENT DATA STRUCTURE")
    print("=" * 50)
    
    # Get a sample patient
    patients = Patient.objects.select_related('user').all()[:3]
    
    print(f"Total patients: {Patient.objects.count()}")
    
    if patients:
        for patient in patients:
            print(f"\nPatient ID: {patient.id}")
            print(f"  User ID: {patient.user.id}")
            print(f"  User first_name: '{patient.user.first_name}'")
            print(f"  User last_name: '{patient.user.last_name}'")
            print(f"  User email: '{patient.user.email}'")
            print(f"  User phone: '{getattr(patient.user, 'phone_number', 'N/A')}'")
            print(f"  Patient age: {patient.age}")
            print(f"  Patient gender: '{patient.gender}'")
            
            # Test name construction
            full_name = f"{patient.user.first_name or ''} {patient.user.last_name or ''}".strip()
            print(f"  Constructed name: '{full_name}'")
            
            if not full_name:
                print(f"  ⚠️  WARNING: Patient {patient.id} has no name!")
            else:
                print(f"  ✅ Patient name OK: {full_name}")
    else:
        print("No patients found in database")
    
    return True

def test_doctor_data_structure():
    """Test doctor data structure for name display"""
    print("=" * 50)
    print("TESTING DOCTOR DATA STRUCTURE")
    print("=" * 50)
    
    # Get a sample doctor
    doctors = Doctor.objects.select_related('user', 'specialization').all()[:3]
    
    print(f"Total doctors: {Doctor.objects.count()}")
    
    if doctors:
        for doctor in doctors:
            print(f"\nDoctor ID: {doctor.id}")
            print(f"  User ID: {doctor.user.id}")
            print(f"  User first_name: '{doctor.user.first_name}'")
            print(f"  User last_name: '{doctor.user.last_name}'")
            print(f"  User email: '{doctor.user.email}'")
            print(f"  User phone: '{getattr(doctor.user, 'phone_number', 'N/A')}'")
            print(f"  Specialization: {doctor.specialization.name if doctor.specialization else 'None'}")
            print(f"  License: '{doctor.license_number}'")
            print(f"  Qualification: '{doctor.qualification}'")
            
            # Test name construction
            full_name = f"Dr. {doctor.user.first_name or ''} {doctor.user.last_name or ''}".strip()
            print(f"  Constructed name: '{full_name}'")
            
            if full_name == 'Dr.' or not full_name:
                print(f"  ⚠️  WARNING: Doctor {doctor.id} has no name!")
            else:
                print(f"  ✅ Doctor name OK: {full_name}")
    else:
        print("No doctors found in database")
    
    return True

def test_admin_serializers():
    """Test admin serializers for creating patients and doctors"""
    print("=" * 50)
    print("TESTING ADMIN SERIALIZERS")
    print("=" * 50)
    
    # Test patient serializer
    print("Testing AdminCreatePatientSerializer...")
    patient_data = {
        'user': {
            'username': 'test_patient_admin',
            'email': 'test_patient_admin@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'Patient',
            'phone_number': '+1234567890',
            'address': '123 Test St'
        },
        'age': 30,
        'gender': 'male',
        'blood_group': 'O+',
        'height': 175.0,
        'weight': 70.0
    }
    
    patient_serializer = AdminCreatePatientSerializer(data=patient_data)
    if patient_serializer.is_valid():
        print("✅ Patient serializer validation passed")
        # Don't actually create to avoid duplicates
        # patient = patient_serializer.save()
        # print(f"✅ Patient created: {patient}")
    else:
        print("❌ Patient serializer validation failed:")
        print(f"  Errors: {patient_serializer.errors}")
    
    # Test doctor serializer
    print("\nTesting AdminCreateDoctorSerializer...")
    
    # Get first specialization
    specialization = Specialization.objects.first()
    if not specialization:
        print("❌ No specializations found. Creating one...")
        specialization = Specialization.objects.create(
            name='General Medicine',
            description='General medical practice'
        )
    
    doctor_data = {
        'user': {
            'username': 'test_doctor_admin',
            'email': 'test_doctor_admin@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'Doctor',
            'phone_number': '+1234567891',
            'address': '456 Test Ave'
        },
        'specialization': specialization.id,
        'license_number': 'LIC123456',
        'qualification': 'MBBS, MD',
        'years_of_experience': 5,
        'consultation_fee': 100.00,
        'bio': 'Test doctor bio',
        'is_available': True,
        'is_verified': True
    }
    
    doctor_serializer = AdminCreateDoctorSerializer(data=doctor_data)
    if doctor_serializer.is_valid():
        print("✅ Doctor serializer validation passed")
        # Don't actually create to avoid duplicates
        # doctor = doctor_serializer.save()
        # print(f"✅ Doctor created: {doctor}")
    else:
        print("❌ Doctor serializer validation failed:")
        print(f"  Errors: {doctor_serializer.errors}")
    
    return True

def main():
    """Run all tests"""
    print("🔧 ADMIN FUNCTIONALITY TEST SUITE")
    print("=" * 60)
    
    try:
        test_specializations()
        test_patient_data_structure()
        test_doctor_data_structure()
        test_admin_serializers()
        
        print("=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()