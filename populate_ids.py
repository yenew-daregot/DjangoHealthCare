import os
import sys
import django

# Set the correct Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Setup Django
django.setup()

from doctors.models import Doctor
from django.db.models import Q

def populate_ids():
    print("🔍 Starting to populate doctor IDs...")
    
    # Get all doctors ordered by creation date
    all_doctors = Doctor.objects.order_by('created_at', 'id').all()
    total_count = all_doctors.count()
    
    print(f"📊 Found {total_count} doctors in the database")
    
    if total_count == 0:
        print("❌ No doctors found in the database.")
        return
    
    # Show current state
    print("\n📋 Current doctors (before update):")
    print("-" * 50)
    for doc in all_doctors:
        status = doc.doctor_id if doc.doctor_id else "❌ NO ID"
        print(f"  👨‍⚕️  {doc.id}: {doc.full_name} -> {status}")
    
    # Find the highest existing sequential number
    max_number = 0
    doctors_with_ids = Doctor.objects.exclude(
        Q(doctor_id__isnull=True) | Q(doctor_id__exact='')
    )
    
    for doctor in doctors_with_ids:
        if doctor.doctor_id and doctor.doctor_id.startswith('DOC'):
            try:
                # Extract number from DOC00001 format
                num_str = doctor.doctor_id[3:]
                if num_str.isdigit():
                    num = int(num_str)
                    if num > max_number:
                        max_number = num
            except ValueError:
                continue
    
    print(f"\n🎯 Highest existing doctor ID number: DOC{max_number:05d}")
    print(f"🔄 Starting sequential numbering from: DOC{(max_number + 1):05d}")
    
    # Process each doctor
    counter = max_number + 1
    updated_count = 0
    
    print("\n🔄 Processing doctors:")
    print("-" * 50)
    
    for doctor in all_doctors:
        needs_update = False
        reason = ""
        
        if not doctor.doctor_id:
            needs_update = True
            reason = "No ID assigned"
        elif doctor.doctor_id == '':
            needs_update = True
            reason = "Empty ID"
        elif not doctor.doctor_id.startswith('DOC'):
            needs_update = True
            reason = f"Non-standard ID: {doctor.doctor_id}"
        elif len(doctor.doctor_id) != 8:  # DOC + 5 digits = 8 characters
            needs_update = True
            reason = f"Malformed ID length: {doctor.doctor_id}"
        else:
            # Check if it's already a valid sequential ID
            try:
                current_num = int(doctor.doctor_id[3:])
                if current_num != counter:
                    needs_update = True
                    reason = f"Non-sequential ID: DOC{current_num:05d}"
            except ValueError:
                needs_update = True
                reason = f"Invalid number format: {doctor.doctor_id}"
        
        if needs_update:
            new_id = f"DOC{counter:05d}"
            print(f"  🔄 {doctor.full_name}")
            print(f"     ❌ {reason}")
            print(f"     ✅ Updating to: {new_id}")
            
            doctor.doctor_id = new_id
            doctor.save(update_fields=['doctor_id'])
            updated_count += 1
            counter += 1
        else:
            # Already has correct sequential ID
            current_num = int(doctor.doctor_id[3:])
            print(f"  ✓ {doctor.full_name} -> {doctor.doctor_id} (Already correct)")
            if current_num >= counter:
                counter = current_num + 1
    
    print(f"\n✅ Updated {updated_count} doctors with sequential IDs")
    
    # Final verification
    print("\n📋 Final verification:")
    print("-" * 50)
    
    doctors_after = Doctor.objects.order_by('doctor_id').all()
    for doc in doctors_after:
        print(f"  {doc.doctor_id}: {doc.full_name}")
    
    # Check for duplicates
    from django.db.models import Count
    duplicates = Doctor.objects.values('doctor_id').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    if duplicates.exists():
        print("\n⚠️  WARNING: Found duplicate doctor IDs!")
        for dup in duplicates:
            print(f"  ❌ {dup['doctor_id']}: {dup['count']} duplicates")
    else:
        print("\n🎉 All doctor IDs are unique!")
    
    # Summary
    total_doctors = Doctor.objects.count()
    unique_ids = Doctor.objects.values('doctor_id').distinct().count()
    
    print(f"\n📊 Summary:")
    print(f"  Total doctors: {total_doctors}")
    print(f"  Unique doctor IDs: {unique_ids}")
    
    if total_doctors == unique_ids:
        print("  ✅ Perfect! All IDs are unique.")
    else:
        print(f"  ❌ Problem: {total_doctors - unique_ids} duplicate(s) found!")

if __name__ == '__main__':
    populate_ids()