#!/usr/bin/env python3
"""
Test script to debug admin patient creation
"""
import os
import sys
import django
import requests
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_admin_create_patient():
    """Test admin patient creation with detailed error reporting"""
    
    # First, let's test if we can get an admin token
    print("=" * 60)
    print("TESTING ADMIN PATIENT CREATION")
    print("=" * 60)
    
    # Test data for patient creation
    patient_data = {
        "user": {
            "username": "testpatient123",
            "email": "testpatient123@example.com",
            "first_name": "Test",
            "last_name": "Patient",
            "phone": "1234567890",
            "password": "testpass123",
            "confirm_password": "testpass123"
        },
        "age": 30,
        "gender": "male",
        "blood_group": "O+",
        "emergency_contact": "Emergency Contact",
        "emergency_contact_phone": "0987654321"
    }
    
    print("Test data:")
    print(json.dumps(patient_data, indent=2))
    print("-" * 40)
    
    # Try to create patient without authentication first
    url = "http://127.0.0.1:8000/api/admin/create-patient/"
    
    try:
        print(f"Testing endpoint: {url}")
        
        # Test without authentication
        response = requests.post(url, json=patient_data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print("Response JSON:")
            print(json.dumps(response_data, indent=2))
        except:
            print("Response Text:")
            print(response.text[:500])
        
        print("-" * 40)
        
        # Now let's try to get an admin token and test with authentication
        print("Attempting to get admin token...")
        
        # Try to login as admin (you'll need to have an admin user)
        login_url = "http://127.0.0.1:8000/api/auth/token/"
        login_data = {
            "username": "admin",  # Change this to your admin username
            "password": "admin123"  # Change this to your admin password
        }
        
        login_response = requests.post(login_url, json=login_data, timeout=10)
        print(f"Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            access_token = token_data.get('access')
            
            if access_token:
                print("✅ Got admin token successfully")
                
                # Test with authentication
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
                
                print("Testing with authentication...")
                auth_response = requests.post(url, json=patient_data, headers=headers, timeout=10)
                print(f"Authenticated Status Code: {auth_response.status_code}")
                
                try:
                    auth_response_data = auth_response.json()
                    print("Authenticated Response JSON:")
                    print(json.dumps(auth_response_data, indent=2))
                except:
                    print("Authenticated Response Text:")
                    print(auth_response.text[:500])
            else:
                print("❌ No access token in response")
                print(token_data)
        else:
            print("❌ Login failed")
            try:
                print(login_response.json())
            except:
                print(login_response.text[:200])
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {str(e)}")
        print("Make sure the Django server is running on http://127.0.0.1:8000")
    
    print("=" * 60)

if __name__ == "__main__":
    test_admin_create_patient()