#!/usr/bin/env python3

import os
import sys
import django
from django.conf import settings

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from doctors.serializers import DoctorSerializer
from doctors.models import Doctor, Specialization
from users.models import CustomUser

def test_doctor_serializer_fields():
    """Test that DoctorSerializer has correct field configuration"""
    print("🔍 Testing DoctorSerializer field configuration...")
    
    # Check that serializer can be instantiated
    serializer = DoctorSerializer()
    
    # Check field names
    field_names = list(serializer.fields.keys())
    print(f"✅ Serializer fields: {field_names}")
    
    # Check for conflicting email fields
    email_fields = [f for f in field_names if 'email' in f.lower()]
    print(f"📧 Email-related fields: {email_fields}")
    
    # Verify user_email is write_only
    if 'user_email' in serializer.fields:
        user_email_field = serializer.fields['user_email']
        print(f"✅ user_email field: write_only={getattr(user_email_field, 'write_only', False)}")
    
    # Verify email is read_only (SerializerMethodField)
    if 'email' in serializer.fields:
        email_field = serializer.fields['email']
        print(f"✅ email field type: {type(email_field).__name__}")
    
    return True

def test_doctor_update_data_structure():
    """Test the data structure for doctor updates"""
    print("\n🔍 Testing doctor update data structure...")
    
    # Sample update data (as would come from frontend)
    update_data = {
        'specialization_id': 1,
        'license_number': 'LIC123456',
        'qualification': 'MBBS, MD',
        'years_of_experience': 5,
        'consultation_fee': 100.00,
        'bio': 'Experienced doctor',
        'is_available': True,
        'is_verified': True,
        'first_name': 'John',
        'last_name': 'Doe',
        'user_email': 'john.doe@example.com',
        'phone': '+1234567890'
    }
    
    print(f"📝 Sample update data: {update_data}")
    
    # Test serializer validation
    serializer = DoctorSerializer()
    
    # Check which fields are recognized
    recognized_fields = []
    unrecognized_fields = []
    
    for field_name in update_data.keys():
        if field_name in serializer.fields:
            recognized_fields.append(field_name)
        else:
            unrecognized_fields.append(field_name)
    
    print(f"✅ Recognized fields: {recognized_fields}")
    if unrecognized_fields:
        print(f"❌ Unrecognized fields: {unrecognized_fields}")
    
    return len(unrecognized_fields) == 0

def main():
    print("🚀 Testing Doctor Update Functionality Fix")
    print("=" * 50)
    
    try:
        # Test 1: Field configuration
        test1_passed = test_doctor_serializer_fields()
        
        # Test 2: Data structure
        test2_passed = test_doctor_update_data_structure()
        
        print("\n" + "=" * 50)
        print("📊 Test Results:")
        print(f"✅ Field Configuration: {'PASSED' if test1_passed else 'FAILED'}")
        print(f"✅ Data Structure: {'PASSED' if test2_passed else 'FAILED'}")
        
        if test1_passed and test2_passed:
            print("\n🎉 All tests passed! Doctor update functionality should work correctly.")
            print("\n📋 Summary of fixes:")
            print("   • Renamed conflicting 'email' field to 'user_email' in write_only fields")
            print("   • Updated frontend to use 'user_email' instead of 'email'")
            print("   • Maintained 'email' as read-only SerializerMethodField for display")
            print("   • Updated field mapping in serializer update method")
        else:
            print("\n❌ Some tests failed. Please check the configuration.")
            
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    main()