#!/usr/bin/env python
"""
Test script to diagnose doctor profile issue
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from doctors.models import Doctor

User = get_user_model()

def test_doctor_profile_issue():
    """Test doctor profile availability"""
    print("🔍 Diagnosing Doctor Profile Issue...")
    
    # Check all users with DOCTOR role
    try:
        doctor_users = User.objects.filter(role='DOCTOR')
        print(f"✅ Found {doctor_users.count()} users with DOCTOR role:")
        
        for user in doctor_users:
            print(f"   - {user.username} ({user.email}) - {user.first_name} {user.last_name}")
            
            # Check if they have a doctor profile
            try:
                doctor = Doctor.objects.get(user=user)
                print(f"     ✅ Has doctor profile: ID {doctor.id}")
                print(f"        - Specialization: {doctor.specialization}")
                print(f"        - Available: {doctor.is_available}")
                print(f"        - Verified: {doctor.is_verified}")
            except Doctor.DoesNotExist:
                print(f"     ❌ NO DOCTOR PROFILE FOUND!")
                
                # Create a basic doctor profile
                try:
                    doctor = Doctor.objects.create(
                        user=user,
                        qualification='MBBS',
                        years_of_experience=5,
                        consultation_fee=500,
                        is_available=True,
                        is_verified=True
                    )
                    print(f"     ✅ Created doctor profile: ID {doctor.id}")
                except Exception as e:
                    print(f"     ❌ Failed to create doctor profile: {e}")
    
    except Exception as e:
        print(f"❌ Error checking doctor users: {e}")
        return False
    
    # Check all doctor profiles
    try:
        all_doctors = Doctor.objects.all()
        print(f"\n✅ Total doctor profiles in database: {all_doctors.count()}")
        
        for doctor in all_doctors:
            print(f"   - Doctor ID {doctor.id}: {doctor.user.username} ({doctor.user.email})")
            print(f"     Full name: {doctor.full_name}")
            print(f"     Specialization: {doctor.specialization}")
            print(f"     Available: {doctor.is_available}")
            print(f"     Verified: {doctor.is_verified}")
    
    except Exception as e:
        print(f"❌ Error checking doctor profiles: {e}")
        return False
    
    print("\n🎉 Doctor profile diagnosis complete!")
    return True

def create_test_doctor():
    """Create a test doctor if none exists"""
    print("\n🏥 Creating test doctor...")
    
    try:
        # Get or create a doctor user
        user, created = User.objects.get_or_create(
            username='testdoctor',
            defaults={
                'email': 'testdoctor@example.com',
                'first_name': 'Test',
                'last_name': 'Doctor',
                'role': 'DOCTOR'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✅ Created test user: {user.username}")
        else:
            print(f"✅ Using existing user: {user.username}")
        
        # Create or get doctor profile
        doctor, created = Doctor.objects.get_or_create(
            user=user,
            defaults={
                'qualification': 'MBBS, MD',
                'years_of_experience': 10,
                'consultation_fee': 1000,
                'is_available': True,
                'is_verified': True,
                'bio': 'Test doctor for debugging purposes'
            }
        )
        
        if created:
            print(f"✅ Created test doctor profile: ID {doctor.id}")
        else:
            print(f"✅ Using existing doctor profile: ID {doctor.id}")
        
        return doctor
        
    except Exception as e:
        print(f"❌ Error creating test doctor: {e}")
        return None

if __name__ == '__main__':
    print("=" * 60)
    print("🏥 DOCTOR PROFILE ISSUE DIAGNOSIS")
    print("=" * 60)
    
    # Test doctor profile issue
    test_doctor_profile_issue()
    
    # Create test doctor if needed
    create_test_doctor()
    
    print("\n" + "=" * 60)
    print("✅ Diagnosis complete!")
    print("If you're still seeing 'Profile Not Found', try:")
    print("1. Make sure you're logged in as a user with DOCTOR role")
    print("2. Check that the user has a corresponding Doctor profile")
    print("3. Verify the API endpoint is working: GET /api/doctors/profile/")
    print("=" * 60)