#!/usr/bin/env python3
"""
Debug admin create patient issue
"""
import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_dashboard.serializers import AdminCreatePatientSerializer, AdminCreateDoctorSerializer
from users.models import CustomUser

def test_serializers():
    print("=" * 60)
    print("TESTING ADMIN SERIALIZERS")
    print("=" * 60)
    
    # Test patient data
    patient_data = {
        "user": {
            "username": "testpatient456",
            "email": "testpatient456@example.com",
            "first_name": "Test",
            "last_name": "Patient",
            "phone_number": "1234567890",
            "password": "testpass123",
            "confirm_password": "testpass123"
        },
        "age": 30,
        "gender": "male",
        "blood_group": "O+"
    }
    
    print("Testing AdminCreatePatientSerializer...")
    print("Data:", patient_data)
    
    try:
        serializer = AdminCreatePatientSerializer(data=patient_data)
        print(f"Is valid: {serializer.is_valid()}")
        
        if not serializer.is_valid():
            print("Validation errors:")
            for field, errors in serializer.errors.items():
                print(f"  {field}: {errors}")
        else:
            print("✅ Serializer validation passed!")
            
            # Try to save
            try:
                patient = serializer.save()
                print(f"✅ Patient created: {patient}")
            except Exception as e:
                print(f"❌ Error saving: {str(e)}")
                import traceback
                print(traceback.format_exc())
                
    except Exception as e:
        print(f"❌ Error with serializer: {str(e)}")
        import traceback
        print(traceback.format_exc())
    
    print("-" * 40)
    
    # Test doctor data
    doctor_data = {
        "user": {
            "username": "testdoctor456",
            "email": "testdoctor456@example.com",
            "first_name": "Test",
            "last_name": "Doctor",
            "phone_number": "1234567890",
            "password": "testpass123",
            "confirm_password": "testpass123"
        },
        "specialization": "General Medicine",
        "qualification": "MD",
        "years_of_experience": 5,
        "consultation_fee": 500
    }
    
    print("Testing AdminCreateDoctorSerializer...")
    print("Data:", doctor_data)
    
    try:
        serializer = AdminCreateDoctorSerializer(data=doctor_data)
        print(f"Is valid: {serializer.is_valid()}")
        
        if not serializer.is_valid():
            print("Validation errors:")
            for field, errors in serializer.errors.items():
                print(f"  {field}: {errors}")
        else:
            print("✅ Serializer validation passed!")
            
            # Try to save
            try:
                doctor = serializer.save()
                print(f"✅ Doctor created: {doctor}")
            except Exception as e:
                print(f"❌ Error saving: {str(e)}")
                import traceback
                print(traceback.format_exc())
                
    except Exception as e:
        print(f"❌ Error with serializer: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_serializers()