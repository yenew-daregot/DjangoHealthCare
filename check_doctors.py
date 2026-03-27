#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from doctors.models import Doctor

# Check doctor data
doctors = Doctor.objects.all()
print(f'Total doctors: {doctors.count()}')
print(f'Available doctors: {doctors.filter(is_available=True).count()}')
print(f'Verified doctors: {doctors.filter(is_verified=True).count()}')
print(f'Available AND verified: {doctors.filter(is_available=True, is_verified=True).count()}')

print('\nDoctor details:')
for d in doctors[:10]:
    print(f'ID: {d.id}, Name: {d.full_name}, Available: {d.is_available}, Verified: {d.is_verified}')