#!/usr/bin/env python
"""
Script to create Doctor profiles for users with DOCTOR role who don't have one
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from doctors.models import Doctor, Specialization

User = get_user_model()

def create_missing_doctor_profiles():
    """Create Doctor profiles for users with DOCTOR role who don't have one"""
    
    # Get or create a default specialization
    general_spec, created = Specialization.objects.get_or_create(
        name='General Medicine',
        defaults={
            'description': 'General medical practice',
            'is_active': True
        }
    )
    
    if created:
        print(f"Created default specialization: {general_spec.name}")
    
    # Find users with DOCTOR role who don't have Doctor profiles
    doctor_users = User.objects.filter(role='DOCTOR')
    created_count = 0
    
    for user in doctor_users:
        try:
            # Check if doctor profile already exists
            doctor = Doctor.objects.get(user=user)
            print(f"✓ User {user.username} already has doctor profile: {doctor.doctor_id}")
        except Doctor.DoesNotExist:
            # Create doctor profile
            try:
                doctor = Doctor.objects.create(
                    user=user,
                    specialization=general_spec,
                    license_number=f"LIC{user.id:06d}",  # Generate unique license number
                    qualification="Medical Degree",  # Default qualification
                    years_of_experience=5,  # Default experience
                    consultation_fee=500.00,  # Default fee
                    is_available=True,
                    is_verified=True,  # Set to True for existing users
                    bio=f"Dr. {user.get_full_name() or user.username} is a qualified medical practitioner.",
                    address="Medical Center"
                )
                created_count += 1
                print(f"✓ Created doctor profile for {user.username}: {doctor.doctor_id}")
            except Exception as e:
                print(f"✗ Failed to create doctor profile for {user.username}: {str(e)}")
    
    print(f"\nSummary:")
    print(f"- Total users with DOCTOR role: {doctor_users.count()}")
    print(f"- Doctor profiles created: {created_count}")
    print(f"- Total doctor profiles now: {Doctor.objects.count()}")

if __name__ == '__main__':
    print("Creating missing doctor profiles...")
    create_missing_doctor_profiles()
    print("Done!")