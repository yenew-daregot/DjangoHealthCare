#!/usr/bin/env python
"""
Check emergency database setup
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
    
    from emergency.models import EmergencyRequest, EmergencyContact
    from patients.models import Patient
    from users.models import CustomUser
    
    print("✅ Models imported successfully")
    
    # Check if tables exist by trying to count records
    try:
        user_count = CustomUser.objects.count()
        patient_count = Patient.objects.count()
        emergency_count = EmergencyRequest.objects.count()
        contact_count = EmergencyContact.objects.count()
        
        print(f"📊 Database counts:")
        print(f"   Users: {user_count}")
        print(f"   Patients: {patient_count}")
        print(f"   Emergency Requests: {emergency_count}")
        print(f"   Emergency Contacts: {contact_count}")
        
        # Check if there are any patients with PATIENT role
        patient_users = CustomUser.objects.filter(role='PATIENT')
        print(f"   Patient Users: {patient_users.count()}")
        
        if patient_users.exists():
            print("✅ Patient users found")
            for user in patient_users[:3]:  # Show first 3
                try:
                    patient = Patient.objects.get(user=user)
                    print(f"   - {user.username} has patient profile")
                except Patient.DoesNotExist:
                    print(f"   - {user.username} missing patient profile")
        else:
            print("⚠️ No patient users found")
            
    except Exception as e:
        print(f"❌ Database query error: {e}")
        
except Exception as e:
    print(f"❌ Setup error: {e}")
    import traceback
    traceback.print_exc()