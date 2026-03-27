#!/usr/bin/env python
"""
Fix prescription migration issues by ensuring proper field defaults
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from prescriptions.models import Prescription
from django.utils import timezone

def fix_prescription_migration():
    """Fix prescription migration issues"""
    print("🔧 Fixing prescription migration issues...")
    
    try:
        # Check if the table exists
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'prescriptions_prescription' 
                AND column_name IN ('doctor_id', 