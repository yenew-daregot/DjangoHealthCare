#!/usr/bin/env python
"""
Simple test for emergency functionality
"""
import requests
import json

BASE_URL = 'http://localhost:8000/api'

def test_emergency_endpoints():
    """Test emergency endpoints"""
    print("🧪 Testing Emergency Endpoints...")
    
    # Test emergency root endpoint
    try:
        response = requests.get(f'{BASE_URL}/emergency/')
        print(f"✅ Emergency root endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Available endpoints: {len(data.get('endpoints', {}))}")
        else:
            print(f"❌ Emergency root failed: {response.text}")
    except Exception as e:
        print(f"❌ Emergency root error: {e}")
    
    # Test auth endpoint
    try:
        auth_data = {
            'username': 'admin',
            'password': 'admin'
        }
        response = requests.post(f'{BASE_URL}/auth/token/', json=auth_data)
        print(f"🔐 Auth test: {response.status_code}")
        
        if response.status_code == 200:
            token = response.json().get('access')
            print(f"✅ Got auth token")
            
            # Test emergency requests endpoint with auth
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(f'{BASE_URL}/emergency/requests/', headers=headers)
            print(f"📋 Emergency requests: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Emergency requests count: {len(data.get('results', []))}")
            else:
                print(f"❌ Emergency requests failed: {response.text}")
                
        else:
            print(f"❌ Auth failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Auth error: {e}")

if __name__ == '__main__':
    test_emergency_endpoints()