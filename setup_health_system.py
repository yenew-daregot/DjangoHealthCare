#!/usr/bin/env python3
"""
Setup script for Health Monitoring System
Creates necessary database tables and initial data
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

from django.core.management import execute_from_command_line
from health.models import VitalType

def setup_health_system():
    """Setup the health monitoring system"""
    print("Setting up Health Monitoring System...")
    
    try:
        # Create migrations for health app
        print("Creating health app migrations...")
        execute_from_command_line(['manage.py', 'makemigrations', 'health'])
        
        # Apply migrations
        print("Applying health migrations...")
        execute_from_command_line(['manage.py', 'migrate', 'health'])
        
        # Create initial vital types
        print("Creating initial vital types...")
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
            },
            {
                'name': 'weight',
                'display_name': 'Weight',
                'unit': 'kg',
                'normal_min': 20,
                'normal_max': 200,
                'critical_min': 15,
                'critical_max': 250
            },
            {
                'name': 'height',
                'display_name': 'Height',
                'unit': 'cm',
                'normal_min': 100,
                'normal_max': 220,
                'critical_min': 80,
                'critical_max': 250
            },
            {
                'name': 'bmi',
                'display_name': 'Body Mass Index',
                'unit': 'kg/m²',
                'normal_min': 18.5,
                'normal_max': 24.9,
                'critical_min': 10,
                'critical_max': 50
            }
        ]
        
        for vital_data in vital_types_data:
            vital_type, created = VitalType.objects.get_or_create(
                name=vital_data['name'],
                defaults=vital_data
            )
            if created:
                print(f"Created vital type: {vital_type.display_name}")
            else:
                print(f"Vital type already exists: {vital_type.display_name}")
        
        print("\n✅ Health Monitoring System setup completed successfully!")
        print("\nNext steps:")
        print("1. Add 'health' to INSTALLED_APPS in settings.py")
        print("2. Run: python manage.py migrate")
        print("3. Start the development server")
        print("4. Access the health monitoring dashboard")
        
    except Exception as e:
        print(f"❌ Error setting up health system: {e}")
        return False
    
    return True

if __name__ == '__main__':
    setup_health_system()