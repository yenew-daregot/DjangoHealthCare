#!/usr/bin/env python3
"""
Test script to verify specializations API endpoint
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/workspaces/healthcare-management-system/backend')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from doctors.models import Specialization
import json

User = get_user_model()

def test_specializations_api():
    """Test the specializations API endpoint"""
    print("=" * 60)
    print("TESTING SPECIALIZATIONS API ENDPOINT")
    print("=" * 60)
    
    # Create test client
    client = Client()
    
    # Create admin user for authentication
    admin_user, created = User.objects.get_or_create(
        username='test_admin_spec',
        defaults={
            'email': 'test_admin_spec@example.com',
            'role': 'ADMIN',
            'first_name': 'Test',
            'last_name': 'Admin'
        }
    )
    if created:
        admin_user.set_password('testpass123')
        admin_user.save()
    
    # Login
    login_success = client.login(username='test_admin_spec', password='testpass123')
    print(f"Login successful: {login_success}")
    
    if not login_success:
        print("❌ Failed to login admin user")
        return False
    
    # Check existing specializations
    existing_specs = Specialization.objects.all()
    print(f"Existing specializations in database: {existing_specs.count()}")
    
    for spec in existing_specs:
        print(f"  - ID: {spec.id}, Name: '{spec.name}', Active: {spec.is_active}")
    
    # Create some test specializations if none exist
    if existing_specs.count() == 0:
        print("Creating test specializations...")
        test_specs = [
            'General Medicine',
            'Cardiology',
            'Dermatology',
            'Neurology',
            'Orthopedics'
        ]
        
        for spec_name in test_specs:
            spec = Specialization.objects.create(
                name=spec_name,
                description=f'Specialization in {spec_name}',
                is_active=True
            )
            print(f"  Created: {spec.id} - {spec.name}")
    
    # Test the API endpoint
    print(f"\nTesting API endpoint: /api/doctors/specializations/")
    response = client.get('/api/doctors/specializations/')
    
    print(f"Response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Response data type: {type(data)}")
            print(f"Response data: {json.dumps(data, indent=2, default=str)}")
            
            # Check if it's a paginated response
            if isinstance(data, dict) and 'results' in data:
                specializations = data['results']
                print(f"✅ Paginated response with {len(specializations)} specializations")
            elif isinstance(data, list):
                specializations = data
                print(f"✅ Direct list response with {len(specializations)} specializations")
            else:
                print(f"❌ Unexpected response format: {type(data)}")
                return False
            
            # Validate specialization structure
            for i, spec in enumerate(specializations):
                if not isinstance(spec, dict):
                    print(f"❌ Specialization {i} is not a dict: {type(spec)}")
                    continue
                
                if 'id' not in spec or 'name' not in spec:
                    print(f"❌ Specialization {i} missing required fields: {spec}")
                    continue
                
                print(f"  ✅ Specialization {i}: ID={spec['id']}, Name='{spec['name']}'")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Raw response: {response.content}")
            return False
    else:
        print(f"❌ API request failed with status {response.status_code}")
        print(f"Response content: {response.content}")
        return False

def test_specializations_with_different_users():
    """Test specializations API with different user roles"""
    print("=" * 60)
    print("TESTING SPECIALIZATIONS API WITH DIFFERENT USER ROLES")
    print("=" * 60)
    
    client = Client()
    
    # Test with different user roles
    test_users = [
        ('admin', 'ADMIN'),
        ('doctor', 'DOCTOR'),
        ('patient', 'PATIENT'),
    ]
    
    for username, role in test_users:
        print(f"\nTesting with {role} user...")
        
        # Create user
        user, created = User.objects.get_or_create(
            username=f'test_{username}_spec',
            defaults={
                'email': f'test_{username}_spec@example.com',
                'role': role,
                'first_name': 'Test',
                'last_name': role.title()
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
        
        # Login
        login_success = client.login(username=f'test_{username}_spec', password='testpass123')
        
        if login_success:
            response = client.get('/api/doctors/specializations/')
            print(f"  {role} user - Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict) and 'results' in data:
                        count = len(data['results'])
                    elif isinstance(data, list):
                        count = len(data)
                    else:
                        count = 'unknown'
                    print(f"  ✅ {role} user can access specializations: {count} items")
                except:
                    print(f"  ❌ {role} user got invalid JSON response")
            else:
                print(f"  ❌ {role} user access denied: {response.status_code}")
        else:
            print(f"  ❌ Failed to login {role} user")
        
        # Logout
        client.logout()

def main():
    """Run all tests"""
    print("🔧 SPECIALIZATIONS API TEST SUITE")
    print("=" * 70)
    
    try:
        api_result = test_specializations_api()
        test_specializations_with_different_users()
        
        print("=" * 70)
        if api_result:
            print("✅ SPECIALIZATIONS API TESTS COMPLETED SUCCESSFULLY")
        else:
            print("❌ SOME SPECIALIZATIONS API TESTS FAILED")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()