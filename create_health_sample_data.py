#!/usr/bin/env python3
"""
Create sample data for Health Monitoring System
"""

import os
import sys
import django
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from health.models import VitalType, VitalReading, HealthAlert, PatientHealthSummary
from patients.models import Patient
from doctors.models import Doctor

def create_sample_data():
    """Create sample health monitoring data"""
    print("🏥 Creating sample health monitoring data...")
    
    try:
        # Create vital types
        print("\n1. Creating vital types...")
        vital_types_data = [
            {
                'name': 'blood_pressure',
                'display_name': 'Blood Pressure',
                'unit': 'mmHg',
                'normal_min': 90,
                'normal_max': 140,
                'critical_min': 70,
                'critical_max': 180
            },
            {
                'name': 'heart_rate',
                'display_name': 'Heart Rate',
                'unit': 'bpm',
                'normal_min': 60,
                'normal_max': 100,
                'critical_min': 40,
                'critical_max': 150
            },
            {
                'name': 'temperature',
                'display_name': 'Body Temperature',
                'unit': '°C',
                'normal_min': 36.5,
                'normal_max': 37.5,
                'critical_min': 35.0,
                'critical_max': 40.0
            },
            {
                'name': 'oxygen_saturation',
                'display_name': 'Oxygen Saturation',
                'unit': '%',
                'normal_min': 95,
                'normal_max': 100,
                'critical_min': 85,
                'critical_max': 100
            },
            {
                'name': 'respiratory_rate',
                'display_name': 'Respiratory Rate',
                'unit': 'breaths/min',
                'normal_min': 12,
                'normal_max': 20,
                'critical_min': 8,
                'critical_max': 30
            },
            {
                'name': 'blood_sugar',
                'display_name': 'Blood Sugar',
                'unit': 'mg/dL',
                'normal_min': 70,
                'normal_max': 140,
                'critical_min': 40,
                'critical_max': 300
            }
        ]
        
        for vital_data in vital_types_data:
            vital_type, created = VitalType.objects.get_or_create(
                name=vital_data['name'],
                defaults=vital_data
            )
            if created:
                print(f"   Created vital type: {vital_type.display_name}")
            else:
                print(f"   Vital type exists: {vital_type.display_name}")
        
        # Get patients and doctors
        patients = list(Patient.objects.all()[:5])  # Get first 5 patients
        doctors = list(Doctor.objects.all()[:3])    # Get first 3 doctors
        
        if not patients:
            print("   ⚠️  No patients found. Please create some patients first.")
            return False
        
        if not doctors:
            print("   ⚠️  No doctors found. Please create some doctors first.")
            return False
        
        print(f"\n2. Creating sample vital readings for {len(patients)} patients...")
        
        # Create sample vital readings
        vital_types = VitalType.objects.all()
        readings_created = 0
        
        for patient in patients:
            # Create readings for the last 30 days
            for days_ago in range(30, 0, -1):
                reading_date = timezone.now() - timedelta(days=days_ago)
                
                # Create 1-3 readings per day
                num_readings = random.randint(1, 3)
                
                for _ in range(num_readings):
                    vital_type = random.choice(vital_types)
                    doctor = random.choice(doctors)
                    
                    # Generate realistic values
                    if vital_type.name == 'blood_pressure':
                        systolic = random.randint(90, 160)
                        diastolic = random.randint(60, 100)
                        value = f"{systolic}/{diastolic}"
                    elif vital_type.name == 'heart_rate':
                        value = str(random.randint(55, 120))
                    elif vital_type.name == 'temperature':
                        value = str(round(random.uniform(36.0, 38.5), 1))
                    elif vital_type.name == 'oxygen_saturation':
                        value = str(random.randint(88, 100))
                    elif vital_type.name == 'respiratory_rate':
                        value = str(random.randint(10, 25))
                    elif vital_type.name == 'blood_sugar':
                        value = str(random.randint(60, 200))
                    else:
                        value = str(random.randint(50, 150))
                    
                    # Add some random time to the date
                    reading_time = reading_date + timedelta(
                        hours=random.randint(8, 20),
                        minutes=random.randint(0, 59)
                    )
                    
                    vital_reading = VitalReading.objects.create(
                        patient=patient,
                        doctor=doctor,
                        vital_type=vital_type.name,
                        value=value,
                        unit=vital_type.unit,
                        recorded_at=reading_time,
                        notes=f"Sample reading for {patient.user.first_name}",
                        is_manual=True
                    )
                    readings_created += 1
        
        print(f"   Created {readings_created} vital readings")
        
        # Create patient health summaries
        print("\n3. Creating patient health summaries...")
        summaries_created = 0
        
        for patient in patients:
            summary, created = PatientHealthSummary.objects.get_or_create(
                patient=patient,
                defaults={
                    'last_checkup': timezone.now() - timedelta(days=random.randint(1, 30)),
                    'notes': f"Health summary for {patient.user.first_name} {patient.user.last_name}"
                }
            )
            
            if created:
                summary.update_summary()
                summaries_created += 1
                print(f"   Created summary for: {patient.user.first_name} {patient.user.last_name}")
        
        print(f"   Created {summaries_created} patient summaries")
        
        # Final statistics
        print("\n✅ Sample data creation completed!")
        print("\nFinal Statistics:")
        print(f"   - VitalTypes: {VitalType.objects.count()}")
        print(f"   - VitalReadings: {VitalReading.objects.count()}")
        print(f"   - HealthAlerts: {HealthAlert.objects.count()}")
        print(f"   - PatientSummaries: {PatientHealthSummary.objects.count()}")
        print(f"   - Abnormal Readings: {VitalReading.objects.filter(is_abnormal=True).count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = create_sample_data()
    sys.exit(0 if success else 1)