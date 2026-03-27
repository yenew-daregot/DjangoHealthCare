#!/usr/bin/env python3

import os
import sys
import django

# Add the backend directory to Python path
sys.path.append('.')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from doctors.models import Specialization

def check_and_create_specializations():
    """Check existing specializations and create some if none exist"""
    
    print("=" * 50)
    print("CHECKING SPECIALIZATIONS")
    print("=" * 50)
    
    # Check existing specializations
    existing_specs = Specialization.objects.all()
    print(f"Existing specializations: {existing_specs.count()}")
    
    for spec in existing_specs:
        print(f"  ID: {spec.id}, Name: {spec.name}")
    
    # If no specializations exist, create some common ones
    if existing_specs.count() == 0:
        print("\nNo specializations found. Creating default ones...")
        
        default_specializations = [
            {"name": "General Medicine", "description": "General medical practice"},
            {"name": "Cardiology", "description": "Heart and cardiovascular system"},
            {"name": "Dermatology", "description": "Skin, hair, and nail conditions"},
            {"name": "Neurology", "description": "Nervous system disorders"},
            {"name": "Orthopedics", "description": "Musculoskeletal system"},
            {"name": "Pediatrics", "description": "Medical care for children"},
            {"name": "Psychiatry", "description": "Mental health disorders"},
            {"name": "Radiology", "description": "Medical imaging"},
            {"name": "Surgery", "description": "Surgical procedures"},
            {"name": "Gynecology", "description": "Women's reproductive health"},
        ]
        
        for spec_data in default_specializations:
            spec, created = Specialization.objects.get_or_create(
                name=spec_data["name"],
                defaults={"description": spec_data["description"]}
            )
            if created:
                print(f"  ✅ Created: {spec.name}")
            else:
                print(f"  ⚠️ Already exists: {spec.name}")
    
    # Show final list
    print(f"\nFinal specializations count: {Specialization.objects.count()}")
    for spec in Specialization.objects.all():
        print(f"  ID: {spec.id}, Name: {spec.name}")

if __name__ == '__main__':
    check_and_create_specializations()