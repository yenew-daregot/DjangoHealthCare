#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from appointments.serializers import AppointmentCreateSerializer
from doctors.models import Doctor
from patients.models import Patient

def test_appointment_creation():
    print("Testing appointment creation...")
    
    # Get first available doctor and patient
    try:
        doctor = Doctor.objects.filter(is_available=True, is_verified=True).first()
        patient = Patient.objects.first()
        
        if not doctor:
            print("ERROR: No av