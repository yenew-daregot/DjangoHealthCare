#!/usr/bin/env python
import os
import sys
import django
import json

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from doctors.models import Doctor

User = get_user_model()

# Create a test client
client = Client()

print("=== Testing Doctors API ===")

# Test public endpoint first
print("\n1. Testing public endpoint...")
response = client.get('/api/doctors/public-test/')
print(f"Status: {response.status_code}")
print(f"Response: {response.json() if response.status_code == 200 else response.content}")

# Test doctors endpoint without authentication
print("\n2. Testing doctors endpoint without auth...")
response = client.get('/api/doctors/')
print(f"Status: {response.status_code}")
if response.status_code == 401:
    print("Expected: Authentication required")
else:
    print(f"Response: {response.json() if response.status_code == 200 else response.content}")

# Create a test user and authenticate
print("\n3. Creating test user...")
try:
    # Try to get existing user first
    user = User.objects.filter(username='testpatient').first()
    if not user:
        user = User.objects.create_user(
            username='testpatient',
            email='test@example.com',
            password='testpass123',
            role='PATIENT'
        )
        print(f"Created user: {user.username}")
    else:
        print(f"Using existing user: {user.username}")
    
    # Login the user
    client.force_login(user)
    print(f"Logged in as: {user.username} (role: {user.role})")
    
    # Test doctors endpoint with authentication
    print("\n4. Testing doctors endpoint with patient auth...")
    response = client.get('/api/doctors/')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            print(f"Found {len(data)} doctors")
            for doctor in data[:3]:  # Show first 3
                print(f"  - {doctor.get('full_name', 'Unknown')} (Available: {doctor.get('is_available')}, Verified: {doctor.get('is_verified')})")
        elif isinstance(data, dict) and 'results' in data:
            print(f"Found {len(data['results'])} doctors")
            for doctor in data['results'][:3]:  # Show first 3
                print(f"  - {doctor.get('full_name', 'Unknown')} (Available: {doctor.get('is_available')}, Verified: {doctor.get('is_verified')})")
        else:
            print(f"Response: {data}")
    else:
        print(f"Error: {response.content}")

except Exception as e:
    print(f"Error: {e}")

print("\n=== Test Complete ===")