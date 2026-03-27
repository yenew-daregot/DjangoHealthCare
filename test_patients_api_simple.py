#!/usr/bin/env python3
"""
Simple test to verify patients API is working
"""
import requests
import json

def test_patients_api():
    """Test the patients API endpoint"""
    print("=== Testing Patients API ===")
    
    # Test with a doctor login
    login_data = {
        'username': 'gg',  # Using the first doctor from our test
        'password': 'testpass123'  # This might not work, but let's try
    }
    
    try:
        # Try to login
        print("Attempting to login...")
        login_response = requests.post('http://localhost:8000/api/auth/login/', json=login_data)
        
        if login_response.status_code == 200:
            token = login_response.json().get('access')
            print(f"✓ Login successful")
            
            # Test patients API
            headers = {'Authorization': f'Bearer {token}'}
            patients_response = requests.get('http://localhost:8000/api/patients/', headers=headers)
            
            print(f"Patients API Status: {patients_response.status_code}")
            
            if patients_response.status_code == 200:
                patients_data = patients_response.json()
                print(f"✓ Patients API successful")
                print(f"Response format: {type(patients_data)}")
                
                if isinstance(patients_data, dict):
                    if 'results' in patients_data:
                        patients_list = patients_data['results']
                        print(f"Found {len(patients_list)} patients (paginated)")
                    else:
                        patients_list = [patients_data] if patients_data else []
                        print(f"Found single patient object")
                elif isinstance(patients_data, list):
                    patients_list = patients_data
                    print(f"Found {len(patients_list)} patients (list)")
                else:
                    patients_list = []
                    print(f"Unexpected response format")
                
                # Print patient details
                for i, patient in enumerate(patients_list):
                    user_info = patient.get('user', {})
                    print(f"  Patient {i+1}:")
                    print(f"    ID: {patient.get('id')}")
                    print(f"    Name: {user_info.get('first_name', 'N/A')} {user_info.get('last_name', 'N/A')}")
                    print(f"    Email: {user_info.get('email', 'N/A')}")
                    print(f"    Age: {patient.get('age', 'N/A')}")
                    print(f"    Gender: {patient.get('gender', 'N/A')}")
                    print()
                
            else:
                print(f"✗ Patients API failed: {patients_response.status_code}")
                print(f"Response: {patients_response.text}")
                
        else:
            print(f"✗ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            
            # Try without authentication (should still work for testing)
            print("\nTrying without authentication...")
            patients_response = requests.get('http://localhost:8000/api/patients/')
            print(f"No-auth Status: {patients_response.status_code}")
            if patients_response.status_code != 200:
                print(f"Response: {patients_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server. Make sure the backend is running on localhost:8000")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == '__main__':
    test_patients_api()