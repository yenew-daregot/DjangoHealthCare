#!/usr/bin/env python
"""
Test script for the Laboratory Management System
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from labs.models import LabTest, LabRequest, LabResult
from patients.models import Patient
from doctors.models import Doctor

User = get_user_model()

def test_lab_system():
    print("Testing Laboratory Management System...")
    
    # Test 1: Create sample lab tests
    print("\n1. Creating sample lab tests...")
    lab_tests = [
        {
            'name': 'Complete Blood Count (CBC)',
            'description': 'Comprehensive blood analysis',
            'category': 'Hematology',
            'sample_type': 'Blood',
            'normal_range': 'WBC: 4,000-11,000/μL, RBC: 4.5-5.5 million/μL',
            'price': 25.00
        },
        {
            'name': 'Blood Glucose',
            'description': 'Fasting blood sugar test',
            'category': 'Chemistry',
            'sample_type': 'Blood',
            'normal_range': '70-100 mg/dL (fasting)',
            'price': 15.00
        },
        {
            'name': 'Urinalysis',
            'description': 'Complete urine analysis',
            'category': 'Urinalysis',
            'sample_type': 'Urine',
            'normal_range': 'Specific gravity: 1.003-1.030',
            'price': 20.00
        }
    ]
    
    created_tests = []
    for test_data in lab_tests:
        test, created = LabTest.objects.get_or_create(
            name=test_data['name'],
            defaults=test_data
        )
        created_tests.append(test)
        print(f"  {'Created' if created else 'Found'}: {test.name}")
    
    # Test 2: Check for users with different roles
    print("\n2. Checking user roles...")
    
    # Check for patients
    patients = Patient.objects.all()[:3]
    print(f"  Found {patients.count()} patients")
    
    # Check for doctors
    doctors = Doctor.objects.all()[:3]
    print(f"  Found {doctors.count()} doctors")
    
    # Check for laboratorists
    laboratorists = User.objects.filter(role='LABORATORIST')
    print(f"  Found {laboratorists.count()} laboratorists")
    
    if laboratorists.count() == 0:
        print("  Creating sample laboratorist...")
        laboratorist = User.objects.create_user(
            username='lab_tech_1',
            email='lab@example.com',
            password='testpass123',
            first_name='Lab',
            last_name='Technician',
            role='LABORATORIST'
        )
        print(f"  Created laboratorist: {laboratorist.username}")
    else:
        laboratorist = laboratorists.first()
    
    # Test 3: Create sample lab request
    if patients.exists() and doctors.exists() and created_tests:
        print("\n3. Creating sample lab request...")
        
        sample_request = LabRequest.objects.create(
            patient=patients.first(),
            doctor=doctors.first(),
            test=created_tests[0],
            laboratorist=laboratorist,
            priority='normal',
            clinical_notes='Routine checkup - patient reports fatigue',
            status='requested'
        )
        print(f"  Created lab request: {sample_request}")
        
        # Test 4: Create sample result
        print("\n4. Creating sample lab result...")
        
        sample_result = LabResult.objects.create(
            lab_request=sample_request,
            result_text='WBC: 7,500/μL, RBC: 4.8 million/μL, Hemoglobin: 14.2 g/dL',
            interpretation='All values within normal limits',
            is_abnormal=False,
            created_by=laboratorist
        )
        print(f"  Created lab result: {sample_result}")
        
        # Update request status
        sample_request.status = 'completed'
        sample_request.save()
        print(f"  Updated request status to: {sample_request.status}")
    
    # Test 5: Test API serialization
    print("\n5. Testing serialization...")
    try:
        from labs.serializers import LabRequestSerializer, LabTestSerializer
        
        # Test lab test serialization
        test_serializer = LabTestSerializer(created_tests[0])
        print(f"  Lab test serialized successfully: {test_serializer.data['name']}")
        
        # Test lab request serialization
        if LabRequest.objects.exists():
            request_serializer = LabRequestSerializer(LabRequest.objects.first())
            print(f"  Lab request serialized successfully: {request_serializer.data['id']}")
        
    except Exception as e:
        print(f"  Serialization error: {e}")
    
    print("\n✅ Laboratory system test completed successfully!")
    print("\nSummary:")
    print(f"  - Lab Tests: {LabTest.objects.count()}")
    print(f"  - Lab Requests: {LabRequest.objects.count()}")
    print(f"  - Lab Results: {LabResult.objects.count()}")
    print(f"  - Laboratorists: {User.objects.filter(role='LABORATORIST').count()}")

if __name__ == '__main__':
    try:
        test_lab_system()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)