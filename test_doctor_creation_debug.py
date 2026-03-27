#!/usr/bin/env python3
"""
Debug script to test doctor creation with exact frontend data format
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
from admin_dashboard.serializers import AdminCreateDoctorSerializer
import json

User = get_user_model()

def test_doctor_creation_with_frontend_format():
    """Test doctor creation with exact frontend data format"""
    print("=" * 60)
    print("TESTING DOCTOR CREATION WITH FRONTEND FORMAT")
    print("=" * 60)
    
    # Ensure we have specializations
    specializations = Specialization.objects.all()
    print(f"Available specializations: {specializations.count()}")
    
    if specializations.count() == 0:
        print("Creating test specialization...")
        spec = Specialization.objects.create(
            name='General Medicine',
            description='General medical practice'
        )
        print(f"Created specialization: {spec.id} - {spec.name}")
    else:
        spec = specializations.first()
        print(f"Using existing specialization: {spec.id} - {spec.name}")
    
    # Test data in exact frontend format
    doctor_data = {
        'user': {
            'username': 'test_frontend_doctor',
            'email': 'test_frontend_doctor@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'first_name': 'Frontend',
            'last_name': 'TestDoctor',
            'phone_number': '+1234567890',
            'address': '123 Test Street'
        },
        'specialization': spec.id,  # Integer ID as sent by frontend
        'license_number': 'LIC123456',
        'qualification': 'MBBS, MD',
        'years_of_experience': 5,
        'consultation_fee': 100.00,
        'bio': 'Test doctor created via frontend format',
        'is_available': True,
        'is_verified': True
    }
    
    print(f"\nTest data:")
    print(json.dumps(doctor_data, indent=2, default=str))
    
    print(f"\nSpecialization field type: {type(doctor_data['specialization'])}")
    print(f"Specialization value: {doctor_data['specialization']}")
    
    # Test serializer validation
    print(f"\nTesting serializer validation...")
    serializer = AdminCreateDoctorSerializer(data=doctor_data)
    
    if serializer.is_valid():
        print("✅ Serializer validation PASSED")
        
        # Check if user already exists
        if User.objects.filter(username=doctor_data['user']['username']).exists():
            print("⚠️  User already exists, skipping creation")
        else:
            print("Creating doctor...")
            try:
                doctor = serializer.save()
                print(f"✅ Doctor created successfully: {doctor}")
                print(f"   Doctor ID: {doctor.id}")
                print(f"   User: {doctor.user.username}")
                print(f"   Specialization: {doctor.specialization}")
            except Exception as e:
                print(f"❌ Error creating doctor: {str(e)}")
                import traceback
                traceback.print_exc()
    else:
        print("❌ Serializer validation FAILED")
        print("Validation errors:")
        for field, errors in serializer.errors.items():
            print(f"  {field}: {errors}")
    
    return True

def test_specialization_field_types():
    """Test different specialization field types"""
    print("=" * 60)
    print("TESTING SPECIALIZATION FIELD TYPES")
    print("=" * 60)
    
    spec = Specialization.objects.first()
    if not spec:
        spec = Specialization.objects.create(name='Test Spec', description='Test')
    
    # Test different data types
    test_cases = [
        ("Integer ID", spec.id),
        ("String ID", str(spec.id)),
        ("String name", spec.name),
        ("Float ID", float(spec.id)),
    ]
    
    base_data = {
        'user': {
            'username': 'test_spec_types',
            'email': 'test_spec_types@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'Doctor',
            'phone_number': '+1234567890'
        },
        'license_number': 'LIC123456',
        'qualification': 'MD'
    }
    
    for test_name, spec_value in test_cases:
        print(f"\nTesting {test_name}: {spec_value} (type: {type(spec_value)})")
        
        test_data = base_data.copy()
        test_data['specialization'] = spec_value
        
        serializer = AdminCreateDoctorSerializer(data=test_data)
        if serializer.is_valid():
            print(f"  ✅ Validation passed for {test_name}")
        else:
            print(f"  ❌ Validation failed for {test_name}")
            for field, errors in serializer.errors.items():
                print(f"    {field}: {errors}")

def main():
    """Run all tests"""
    print("🔧 DOCTOR CREATION DEBUG TEST SUITE")
    print("=" * 70)
    
    try:
        test_specialization_field_types()
        test_doctor_creation_with_frontend_format()
        
        print("=" * 70)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()