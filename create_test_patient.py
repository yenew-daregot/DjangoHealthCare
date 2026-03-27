#!/usr/bin/env python
"""
Create a test patient for emergency testing
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
    
    from users.models import CustomUser
    from patients.models import Patient
    
    # Create or get test user
    username = 'testpatient'
    email = 'testpatient@example.com'
    password = 'testpass123'
    
    user, created = CustomUser.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'role': 'PATIENT',
            'first_name': 'Test',
            'last_name': 'Patient'
        }
    )
    
    if created:
        user.set_password(password)
        user.save()
        print(f"✅ Created test user: {username}")
    else:
        print(f"✅ Test user already exists: {username}")
    
    # Create or get patient profile
    patient, created = Patient.objects.get_or_create(
        user=user,
        defaults={
            'age': 30,
            'gender': 'male',
            'emergency_contact': 'John Doe',
            'emergency_contact_phone': '1234567890'
        }
    )
    
    if created:
        print(f"✅ Created patient profile for: {username}")
    else:
        print(f"✅ Patient profile already exists for: {username}")
    
    print(f"\n🔑 Test credentials:")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
    print(f"   Email: {email}")
    print(f"   Role: {user.role}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()