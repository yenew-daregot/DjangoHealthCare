#!/usr/bin/env python3
"""
Check Emergency Data
Simple script to check emergency data and date formats.
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from emergency.models import EmergencyRequest
from django.utils import timezone
import json

def check_emergency_data():
    """Check emergency data in database"""
    print("Checking Emergency Data...")
    print("=" * 40)
    
    # Count emergencies
    total_count = EmergencyRequest.objects.count()
    print(f"Total Emergency Requests: {total_count}")
    
    if total_count == 0:
        print("No emergency requests found. Creating sample data...")
        
        # Create sample emergency with proper dates
        from patients.models import Patient
        from users.models import CustomUser
        
        # Try to get or create a patient
        try:
            patient_user = CustomUser.objects.filter(role='PATIENT').first()
            if not patient_user:
                print("No patient users found. Creating test patient...")
                patient_user = CustomUser.objects.create_user(
                    username='emergency_test_patient',
                    email='emergency_patient@test.com',
                    password='testpass123',
                    role='PATIENT',
                    first_name='Emergency',
                    last_name='Patient',
                    phone='+1234567890'
                )
            
            patient, created = Patient.objects.get_or_create(
                user=patient_user,
                defaults={
                    'date_of_birth': '1990-01-01',
                    'gender': 'M',
                    'blood_type': 'O+',
                    'allergies': 'None',
                    'medical_history': 'Test patient'
                }
            )
            
            # Create emergency with proper timezone-aware dates
            now = timezone.now()
            emergency = EmergencyRequest.objects.create(
                patient=patient,
                location='123 Emergency Test Street',
                latitude=40.7128,
                longitude=-74.0060,
                description='Test emergency for date validation',
                emergency_type='medical',
                priority='medium',
                status='pending',
                created_at=now,
                patient_age=33,
                patient_blood_type='O+',
                medical_notes='Test emergency created by check script'
            )
            
            print(f"Created test emergency: {emergency.request_id}")
            total_count = 1
            
        except Exception as e:
            print(f"Error creating test data: {e}")
            return
    
    # Check existing emergencies
    print(f"\nAnalyzing {total_count} emergency requests...")
    
    for i, emergency in enumerate(EmergencyRequest.objects.all()[:10]):  # Check first 10
        print(f"\nEmergency {i+1}: {emergency.request_id}")
        print(f"  Patient: {emergency.patient.user.get_full_name() if emergency.patient else 'None'}")
        print(f"  Type: {emergency.emergency_type}")
        print(f"  Status: {emergency.status}")
        print(f"  Priority: {emergency.priority}")
        
        # Check date fields
        date_fields = [
            ('created_at', emergency.created_at),
            ('acknowledged_at', emergency.acknowledged_at),
            ('dispatched_at', emergency.dispatched_at),
            ('completed_at', emergency.completed_at)
        ]
        
        for field_name, field_value in date_fields:
            if field_value:
                print(f"  {field_name}: {field_value} (type: {type(field_value)})")
                
                # Test serialization
                try:
                    if hasattr(field_value, 'isoformat'):
                        iso_format = field_value.isoformat()
                        print(f"    ISO format: {iso_format}")
                    else:
                        print(f"    No isoformat method available")
                        
                    # Test JSON serialization
                    json_str = json.dumps(field_value, default=str)
                    print(f"    JSON serializable: {json_str}")
                    
                except Exception as e:
                    print(f"    ERROR serializing {field_name}: {e}")
            else:
                print(f"  {field_name}: None")

def test_api_serialization():
    """Test how the API serializes the data"""
    print("\n" + "=" * 40)
    print("Testing API Serialization")
    print("=" * 40)
    
    from emergency.serializers import EmergencyRequestSerializer
    
    emergencies = EmergencyRequest.objects.all()[:5]
    
    for emergency in emergencies:
        print(f"\nSerializing emergency: {emergency.request_id}")
        
        try:
            serializer = EmergencyRequestSerializer(emergency)
            data = serializer.data
            
            print(f"  Serialization successful")
            print(f"  Keys: {list(data.keys())}")
            
            # Check date fields in serialized data
            date_fields = ['created_at', 'acknowledged_at', 'dispatched_at', 'completed_at']
            for field in date_fields:
                if field in data:
                    value = data[field]
                    print(f"    {field}: {value} (type: {type(value)})")
                    
        except Exception as e:
            print(f"  ERROR serializing: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    try:
        check_emergency_data()
        test_api_serialization()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()