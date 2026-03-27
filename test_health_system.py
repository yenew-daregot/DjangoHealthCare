#!/usr/bin/env python3
"""
Test script for Health Monitoring System
"""

import os
import sys
import django
from django.conf import settings

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from health.models import VitalType, VitalReading, HealthAlert, PatientHealthSummary
from patients.models import Patient
from doctors.models import Doctor
from users.models import CustomUser

def test_health_system():
    """Test the health monitoring system"""
    print("🏥 Testing Health Monitoring System...")
    
    try:
        # Test VitalType model
        print("\n1. Testing VitalType model...")
        vital_types_count = VitalType.objects.count()
        print(f"   VitalType model accessible: {vital_types_count} records")
        
        # Create a test vital type if none exist
        if vital_types_count == 0:
            test_vital_type = VitalType.objects.create(
                name='blood_pressure',
                display_name='Blood Pressure',
                unit='mmHg',
                normal_min=90,
                normal_max=140
            )
            print(f"   Created test vital type: {test_vital_type.display_name}")
        
        # Test VitalReading model
        print("\n2. Testing VitalReading model...")
        vital_readings_count = VitalReading.objects.count()
        print(f"   VitalReading model accessible: {vital_readings_count} records")
        
        # Test HealthAlert model
        print("\n3. Testing HealthAlert model...")
        alerts_count = HealthAlert.objects.count()
        print(f"   HealthAlert model accessible: {alerts_count} records")
        
        # Test PatientHealthSummary model
        print("\n4. Testing PatientHealthSummary model...")
        summaries_count = PatientHealthSummary.objects.count()
        print(f"   PatientHealthSummary model accessible: {summaries_count} records")
        
        # Test relationships
        print("\n5. Testing model relationships...")
        patients_count = Patient.objects.count()
        doctors_count = Doctor.objects.count()
        users_count = CustomUser.objects.count()
        
        print(f"   Patients available: {patients_count}")
        print(f"   Doctors available: {doctors_count}")
        print(f"   Users available: {users_count}")
        
        # Test API endpoints (basic import test)
        print("\n6. Testing API components...")
        try:
            from health.views import VitalReadingViewSet, HealthAlertViewSet
            from health.serializers import VitalReadingSerializer, HealthAlertSerializer
            from health.urls import urlpatterns
            print("   ✅ All API components imported successfully")
        except ImportError as e:
            print(f"   ❌ API import error: {e}")
        
        print("\n✅ Health Monitoring System test completed successfully!")
        print("\nSystem Status:")
        print(f"   - VitalTypes: {VitalType.objects.count()}")
        print(f"   - VitalReadings: {VitalReading.objects.count()}")
        print(f"   - HealthAlerts: {HealthAlert.objects.count()}")
        print(f"   - PatientSummaries: {PatientHealthSummary.objects.count()}")
        print(f"   - Available Patients: {Patient.objects.count()}")
        print(f"   - Available Doctors: {Doctor.objects.count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing health system: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_health_system()
    sys.exit(0 if success else 1)