#!/usr/bin/env python3
"""
Test script to verify admin endpoints are working
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

def test_admin_endpoints():
    """Test admin endpoints"""
    base_url = "http://127.0.0.1:8000/api/admin"
    
    # Test endpoints that don't require authentication first
    endpoints_to_test = [
        "/dashboard-stats/",
        "/analytics/", 
        "/recent-activities/",
        "/pending-actions/",
        "/create-patient/",
        "/create-doctor/",
    ]
    
    print("Testing Admin Endpoints...")
    print("=" * 50)
    
    for endpoint in endpoints_to_test:
        url = f"{base_url}{endpoint}"
        try:
            # Test OPTIONS request (CORS preflight)
            options_response = requests.options(url, timeout=5)
            print(f"OPTIONS {endpoint} - Status: {options_response.status_code}")
            
            # Test GET request (will likely return 401/403 due to auth, but should not be 404)
            get_response = requests.get(url, timeout=5)
            print(f"GET {endpoint} - Status: {get_response.status_code}")
            
            if get_response.status_code == 404:
                print(f"❌ ENDPOINT NOT FOUND: {endpoint}")
            elif get_response.status_code in [401, 403]:
                print(f"✅ ENDPOINT EXISTS (Auth required): {endpoint}")
            elif get_response.status_code == 200:
                print(f"✅ ENDPOINT WORKING: {endpoint}")
            else:
                print(f"⚠️  UNEXPECTED STATUS: {endpoint} - {get_response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ CONNECTION ERROR: {endpoint} - {str(e)}")
        
        print("-" * 30)
    
    print("\nTest completed!")
    print("\nIf you see 404 errors, the admin URLs are not properly configured.")
    print("If you see 401/403 errors, the endpoints exist but require authentication.")

if __name__ == "__main__":
    test_admin_endpoints()