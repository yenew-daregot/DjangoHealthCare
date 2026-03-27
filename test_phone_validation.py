#!/usr/bin/env python3
"""
Test phone number validation specifically
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/workspaces/healthcare-management-system/backend')
django.setup()

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

def test_phone_validation():
    """Test various phone number formats"""
    print("=" * 50)
    print("TESTING PHONE NUMBER VALIDATION")
    print("=" * 50)
    
    test_cases = [
        ("+1234567890", "International with +"),
        ("1234567890", "US format without +"),
        ("123-456-7890", "US format with dashes"),
        ("(123) 456-7890", "US format with parentheses"),
        ("+251 938 667 985", "International with spaces"),
        ("0938587338", "Local format"),
        ("123", "Too short"),
        ("+abc1234567", "Invalid characters"),
        ("", "Empty"),
    ]
    
    for phone, description in test_cases:
        print(f"\nTesting: '{phone}' ({description})")
        
        try:
            # Create a test user with this phone number
            user = User(
                username=f"test_{phone.replace('+', 'plus').replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')}",
                email=f"test_{len(phone)}@example.com",
                phone_number=phone,
                role='PATIENT'
            )
            
            # This will trigger the clean() method
            user.full_clean()
            print(f"  ✅ Valid: {phone}")
            
        except ValidationError as e:
            print(f"  ❌ Invalid: {phone}")
            print(f"     Error: {e.message_dict}")
        except Exception as e:
            print(f"  ❌ Error: {phone}")
            print(f"     Exception: {str(e)}")

def test_admin_create_doctor_with_phone():
    """Test creating doctor through admin API with phone number"""
    print("=" * 50)
    print("TESTING ADMIN DOCTOR CREATION WITH PHONE")
    print("=" * 50)
    
    from doctors.models import Specialization
    from admin_dashboard.serializers import AdminCreateDoctorSerializer
    
    # Ensure specialization exists
    spec, created = Specialization.objects.get_or_create(
        name='Test Specialization',
        defaults={'description': 'Test specialization for phone validation'}
    )
    
    test_phones = [
        "+1234567890",
        "1234567890", 
        "123-456-7890",
        "(123) 456-7890"
    ]
    
    for i, phone in enumerate(test_phones):
        print(f"\nTesting doctor creation with phone: '{phone}'")
        
        doctor_data = {
            'user': {
                'username': f'test_doctor_phone_{i}',
                'email': f'test_doctor_phone_{i}@example.com',
                'password': 'testpass123',
                'confirm_password': 'testpass123',
                'first_name': 'Test',
                'last_name': 'Doctor',
                'phone_number': phone,
                'address': '123 Test St'
            },
            'specialization': spec.id,
            'license_number': f'LIC{i:06d}',
            'qualification': 'MD',
            'years_of_experience': 5,
            'consultation_fee': 100.00,
            'is_available': True,
            'is_verified': True
        }
        
        serializer = AdminCreateDoctorSerializer(data=doctor_data)
        
        if serializer.is_valid():
            print(f"  ✅ Serializer validation passed for: {phone}")
            
            # Check if user already exists
            if User.objects.filter(username=doctor_data['user']['username']).exists():
                print(f"  ⚠️  User already exists, skipping creation")
            else:
                try:
                    doctor = serializer.save()
                    print(f"  ✅ Doctor created successfully with phone: {phone}")
                    print(f"     Doctor: {doctor.user.username}")
                    print(f"     Phone: {doctor.user.phone_number}")
                except Exception as e:
                    print(f"  ❌ Error creating doctor: {str(e)}")
        else:
            print(f"  ❌ Serializer validation failed for: {phone}")
            for field, errors in serializer.errors.items():
                print(f"     {field}: {errors}")

def main():
    """Run all tests"""
    print("🔧 PHONE NUMBER VALIDATION TEST SUITE")
    print("=" * 60)
    
    try:
        test_phone_validation()
        test_admin_create_doctor_with_phone()
        
        print("=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()