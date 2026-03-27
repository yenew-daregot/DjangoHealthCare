#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from doctors.models import Doctor

# Update all doctors to be available and verified
doctors = Doctor.objects.all()
print(f'Found {doctors.count()} doctors')

updated_count = 0
for doctor in doctors:
    if not doctor.is_available or not doctor.is_verified:
        doctor.is_available = True
        doctor.is_verified = True
        doctor.save()
        updated_count += 1
        print(f'Updated doctor: {doctor.full_name} (ID: {doctor.id})')

print(f'\nUpdated {updated_count} doctors to be available and verified')
print(f'Total available and verified doctors: {Doctor.objects.filter(is_available=True, is_verified=True).count()}')