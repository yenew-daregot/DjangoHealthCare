#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from doctors.models import Doctor
from doctors.views import public_doctor_stats
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

def test_public_stats():
    print("Testing public doctor stats endpoint...")
    
    # Create a test request
    factory = RequestFactory()
    request = factory.get('/api/doctors/public-stats/')
    request.user = AnonymousUser()
    
    try:
        response = public_doctor_stats(request)
        print('✅ Public stats endpoint works!')
        print(f'Response status: {response.status_code}')
        print(f'Response data: {response.data}')
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    
    # Also check doctor counts directly
    try:
        total = Doctor.objects.filter(is_verified=True).count()
        available = Doctor.objects.filter(is_available=True, is_verified=True).count()
        verified = Doctor.objects.filter(is_verified=True).count()
        
        print(f'\nDirect counts:')
        print(f'Total verified doctors: {total}')
        print(f'Available doctors: {available}')
        print(f'Verified doctors: {verified}')
        
        # Check all doctors
        all_doctors = Doctor.objects.all().count()
        print(f'All doctors: {all_doctors}')
        
    except Exception as e:
        print(f'❌ Error getting direct counts: {e}')

if __name__ == '__main__':
    test_public_stats()