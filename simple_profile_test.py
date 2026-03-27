#!/usr/bin/env python
"""
Simple test for doctor profile
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from doctors.models import Doctor

User = get_user_model()

# Get a doctor user
doctor_user = User.objects.filter(role='DOCTOR').first()
print(f"Doctor user: {doctor_user.username} ({doctor_user.email})")

# Check if they have a profile
try:
    doctor = Doctor.objects.get(user=doctor_user)
    print(f"Doctor profile found: {doctor.full_name}")
    print(f"Doctor ID: {doctor.doctor_id}")
    print(f"Available: {doctor.is_available}")
    print(f"Verified: {doctor.is_verified}")
except Doctor.DoesNotExist:
    print("No doctor profile found!")

# Test the view logic
from doctors.views import DoctorProfileView
from django.http import HttpRequest
from rest_framework.request import Request

# Create a mock request
request = HttpRequest()
request.user = doctor_user
drf_request = Request(request)

# Test the view
view = DoctorProfileView()
view.request = drf_request

try:
    doctor_obj = view.get_object()
    print(f"View returned doctor: {doctor_obj.full_name}")
except Exception as e:
    print(f"View error: {e}")