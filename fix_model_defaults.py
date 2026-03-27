#!/usr/bin/env python
"""
Fix model default values to avoid migration prompts
"""
import os
import sys
import django

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from django.db import transaction

def fix_chat_notifications():
    """Fix ChatNotification records without title"""
    try:
        from chat.models import ChatNotification
        
        # Update any existing records without title
        updated = ChatNotification.objects.filter(title__isnull=True).update(
            title='Notification'
        )
        
        # Also update empty titles
        updated += ChatNotification.objects.filter(title='').update(
            title='Notification'
        )
        
        print(f"✅ Fixed {updated} ChatNotification records")
        return True
    except Exception as e:
        print(f"❌ Error fixing ChatNotification: {e}")
        return False

def fix_medication_created_at():
    """Fix Medication records without created_at"""
    try:
        from prescriptions.models import Medication
        
        # Update any existing records without created_at
        updated = Medication.objects.filter(created_at__isnull=True).update(
            created_at=timezone.now()
        )
        
        print(f"✅ Fixed {updated} Medication records")
        return True
    except Exception as e:
        print(f"❌ Error fixing Medication: {e}")
        return False

def fix_prescription_created_at():
    """Fix Prescription records without created_at"""
    try:
        from prescriptions.models import Prescription
        
        # Update any existing records without created_at
        updated = Prescription.objects.filter(created_at__isnull=True).update(
            created_at=timezone.now()
        )
        
        print(f"✅ Fixed {updated} Prescription records")
        return True
    except Exception as e:
        print(f"❌ Error fixing Prescription: {e}")
        return False

def fix_prescription_patient_field():
    """Fix Prescription records without patient (should be nullable now)"""
    try:
        from prescriptions.models import Prescription
        
        # Count records without patient
        count = Prescription.objects.filter(patient__isnull=True).count()
        print(f"ℹ️  Found {count} Prescription records without patient (this is now allowed)")
        
        return True
    except Exception as e:
        print(f"❌ Error checking Prescription patient field: {e}")
        return False

@transaction.atomic
def main():
    print("🔧 Healthcare System Model Defaults Fix")
    print("=" * 50)
    
    success = True
    
    # Fix each model issue
    print("1. Fixing ChatNotification titles...")
    success &= fix_chat_notifications()
    
    print("\n2. Fixing Medication created_at fields...")
    success &= fix_medication_created_at()
    
    print("\n3. Fixing Prescription created_at fields...")
    success &= fix_prescription_created_at()
    
    print("\n4. Checking Prescription patient fields...")
    success &= fix_prescription_patient_field()
    
    if success:
        print("\n✅ All model fixes completed successfully!")
        print("You can now run migrations without prompts.")
    else:
        print("\n❌ Some fixes failed. Check the errors above.")
    
    print("\n" + "=" * 50)

if __name__ == '__main__':
    main()