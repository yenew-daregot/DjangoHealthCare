#!/usr/bin/env python3
"""
Simple Health Monitoring System test
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
from health.serializers import VitalReadingSerializer, HealthAlertSerializer
from patients.models import Patient
from doctors.models import Doctor

def simple_health_test():
    """Simple test of health monitoring system"""
    print("🏥 Simple Health Monitoring System Test...")
    
    try:
        # Test models
        print("\n1. Testing Models...")
        print(f"   VitalTypes: {VitalType.objects.count()}")
        print(f"   VitalReadings: {VitalReading.objects.count()}")
        print(f"   HealthAlerts: {HealthAlert.objects.count()}")
        print(f"   PatientSummaries: {PatientHealthSummary.objects.count()}")
        
        # Test serializers
        print("\n2. Testing Serializers...")
        
        # Test VitalReading serializer
        recent_vitals = VitalReading.objects.all()[:5]
        if recent_vitals:
            serializer = VitalReadingSerializer(recent_vitals, many=True)
            print(f"   VitalReading serializer works: {len(serializer.data)} items")
            
            # Show sample data
            if serializer.data:
                sample = serializer.data[0]
                print(f"   Sample vital: {sample.get('vital_type')} = {sample.get('value')} {sample.get('unit')}")
        
        # Test HealthAlert serializer
        recent_alerts = HealthAlert.objects.all()[:3]
        if recent_alerts:
            serializer = HealthAlertSerializer(recent_alerts, many=True)
            print(f"   HealthAlert serializer works: {len(serializer.data)} items")
            
            # Show sample alert
            if serializer.data:
                sample = serializer.data[0]
                print(f"   Sample alert: {sample.get('title')} - {sample.get('severity')}")
        
        # Test relationships
        print("\n3. Testing Relationships...")
        
        # Get a patient with vitals
        patients_with_vitals = Patient.objects.filter(vital_readings__isnull=False).distinct()
        if patients_with_vitals:
            patient = patients_with_vitals[0]
            vitals_count = patient.vital_readings.count()
            alerts_count = patient.health_alerts.count()
            print(f"   Patient {patient.user.first_name} has {vitals_count} vitals and {alerts_count} alerts")
        
        # Get a doctor with recorded vitals
        doctors_with_vitals = Doctor.objects.filter(health_vitals_recorded__isnull=False).distinct()
        if doctors_with_vitals:
            doctor = doctors_with_vitals[0]
            recorded_count = doctor.health_vitals_recorded.count()
            print(f"   Doctor {doctor.user.first_name} recorded {recorded_count} vitals")
        
        # Test abnormal readings
        print("\n4. Testing Abnormal Detection...")
        abnormal_vitals = VitalReading.objects.filter(is_abnormal=True)[:5]
        print(f"   Found {abnormal_vitals.count()} abnormal readings")
        
        for vital in abnormal_vitals:
            print(f"   - {vital.vital_type}: {vital.value} {vital.unit} (Patient: {vital.patient.user.first_name})")
        
        # Test vital types
        print("\n5. Testing Vital Types...")
        vital_types = VitalType.objects.all()
        for vt in vital_types:
            readings_count = VitalReading.objects.filter(vital_type=vt.name).count()
            print(f"   {vt.display_name}: {readings_count} readings")
        
        print("\n✅ Simple health test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in simple health test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = simple_health_test()
    sys.exit(0 if success else 1)