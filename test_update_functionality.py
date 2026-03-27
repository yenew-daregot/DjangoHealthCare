#!/usr/bin/env python3
"""
Test script to verify patient and doctor update functionality
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
from doctors.serializers import DoctorSerializer
from patients.serializers import PatientSerializer
import json

User = get_user_model()

def test_patient_update():
    """Test patient update functionality"""
    print("=" * 60)
    print("TESTING PATIENT UPDATE FUNCTIONALITY")
    print("=" * 60)
    
    # Get a test patient
    patient = Patient.objects.select_related('user').first()
    if not patient:
        print("❌ No patients found in database")
        return False
    
    print(f"Testing update for patient: {patient.user.first_name} {patient.user.last_name}")
    print(f"Current data:")
    print(f"  User ID: {patient.user.id}")
    print(f"  Patient ID: {patient.id}")
    print(f"  Name: {patient.user.first_name} {patient.user.last_name}")
    print(f"  Email: {patient.user.email}")
    print(f"  Phone: {patient.user.phone_number}")
    print(f"  Age: {patient.age}")
    print(f"  Gender: {patient.gender}")
    
    # Test data in frontend format (flat structure)
    update_data = {
        # Patient fields
        'age': 35,
        'gender': 'male',
        'blood_group': 'A+',
        'height': 180.0,
        'weight': 75.0,
        'allergy_notes': 'Updated allergy notes',
        'chronic_conditions': 'Updated chronic conditions',
        # User fields (flat structure)
        'first_name': 'Updated First',
        'last_name': 'Updated Last',
        'email': patient.user.email,  # Keep same email
        'phone': '1234567890',
        'address': 'Updated Address 123'
    }
    
    print(f"\nUpdate data:")
    print(json.dumps(update_data, indent=2, default=str))
    
    # Test serializer update
    serializer = PatientSerializer(patient, data=update_data, partial=True)
    
    if serializer.is_valid():
        print("✅ Patient serializer validation passed")
        
        try:
            updated_patient = serializer.save()
            print(f"✅ Patient updated successfully")
            
            # Refresh from database
            updated_patient.refresh_from_db()
            updated_patient.user.refresh_from_db()
            
            print(f"Updated data:")
            print(f"  Name: {updated_patient.user.first_name} {updated_patient.user.last_name}")
            print(f"  Email: {updated_patient.user.email}")
            print(f"  Phone: {updated_patient.user.phone_number}")
            print(f"  Age: {updated_patient.age}")
            print(f"  Gender: {updated_patient.gender}")
            print(f"  Blood Group: {updated_patient.blood_group}")
            print(f"  Address: {updated_patient.user.address}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating patient: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("❌ Patient serializer validation failed")
        print("Validation errors:")
        for field, errors in serializer.errors.items():
            print(f"  {field}: {errors}")
        return False

def test_doctor_update():
    """Test doctor update functionality"""
    print("=" * 60)
    print("TESTING DOCTOR UPDATE FUNCTIONALITY")
    print("=" * 60)
    
    # Get a test doctor
    doctor = Doctor.objects.select_related('user', 'specialization').first()
    if not doctor:
        print("❌ No doctors found in database")
        return False
    
    print(f"Testing update for doctor: Dr. {doctor.user.first_name} {doctor.user.last_name}")
    print(f"Current data:")
    print(f"  User ID: {doctor.user.id}")
    print(f"  Doctor ID: {doctor.id}")
    print(f"  Name: Dr. {doctor.user.first_name} {doctor.user.last_name}")
    print(f"  Email: {doctor.user.email}")
    print(f"  Phone: {doctor.user.phone_number}")
    print(f"  Specialization: {doctor.specialization.name if doctor.specialization else 'None'}")
    print(f"  License: {doctor.license_number}")
    print(f"  Qualification: {doctor.qualification}")
    
    # Get a specialization for testing
    specialization = Specialization.objects.first()
    if not specialization:
        specialization = Specialization.objects.create(
            name='Test Specialization',
            description='Test specialization for update'
        )
    
    # Test data in frontend format (flat structure)
    update_data = {
        # Doctor fields
        'specialization_id': specialization.id,
        'license_number': 'UPD123456',
        'qualification': 'Updated MBBS, MD',
        'years_of_experience': 10,
        'consultation_fee': 150.00,
        'bio': 'Updated doctor bio',
        'is_available': True,
        'is_verified': True,
        # User fields (flat structure)
        'phone': '9876543210',
        'address': 'Updated Doctor Address 456'
    }
    
    print(f"\nUpdate data:")
    print(json.dumps(update_data, indent=2, default=str))
    
    # Test serializer update
    serializer = DoctorSerializer(doctor, data=update_data, partial=True)
    
    if serializer.is_valid():
        print("✅ Doctor serializer validation passed")
        
        try:
            updated_doctor = serializer.save()
            print(f"✅ Doctor updated successfully")
            
            # Refresh from database
            updated_doctor.refresh_from_db()
            updated_doctor.user.refresh_from_db()
            
            print(f"Updated data:")
            print(f"  Name: Dr. {updated_doctor.user.first_name} {updated_doctor.user.last_name}")
            print(f"  Email: {updated_doctor.user.email}")
            print(f"  Phone: {updated_doctor.user.phone_number}")
            print(f"  Specialization: {updated_doctor.specialization.name if updated_doctor.specialization else 'None'}")
            print(f"  License: {updated_doctor.license_number}")
            print(f"  Qualification: {updated_doctor.qualification}")
            print(f"  Experience: {updated_doctor.years_of_experience} years")
            print(f"  Fee: ${updated_doctor.consultation_fee}")
            print(f"  Address: {updated_doctor.user.address}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating doctor: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("❌ Doctor serializer validation failed")
        print("Validation errors:")
        for field, errors in serializer.errors.items():
            print(f"  {field}: {errors}")
        return False

def main():
    """Run all tests"""
    print("🔧 UPDATE FUNCTIONALITY TEST SUITE")
    print("=" * 70)
    
    try:
        patient_result = test_patient_update()
        doctor_result = test_doctor_update()
        
        print("=" * 70)
        if patient_result and doctor_result:
            print("✅ ALL UPDATE TESTS PASSED")
        else:
            print("❌ SOME UPDATE TESTS FAILED")
            print(f"Patient update: {'✅' if patient_result else '❌'}")
            print(f"Doctor update: {'✅' if doctor_result else '❌'}")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()