#!/usr/bin/env python
"""
Setup script for billing system initial data
Run this script to populate the billing system with sample data
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from billing.models import (
    UniversityProgram, ServiceCategory, StudentInsurance, 
    Invoice, InvoiceItem, Payment, StudentDebt, FeeWaiver
)
from patients.models import Patient
from django.contrib.auth import get_user_model

User = get_user_model()

def create_university_programs():
    """Create sample university programs"""
    programs = [
        {
            'name': 'Computer Science',
            'program_type': 'undergraduate',
            'department': 'Engineering',
            'tuition_coverage': Decimal('75.00')
        },
        {
            'name': 'Medicine',
            'program_type': 'graduate',
            'department': 'Medical School',
            'tuition_coverage': Decimal('90.00')
        },
        {
            'name': 'Business Administration',
            'program_type': 'graduate',
            'department': 'Business School',
            'tuition_coverage': Decimal('60.00')
        },
        {
            'name': 'International Studies',
            'program_type': 'international',
            'department': 'Liberal Arts',
            'tuition_coverage': Decimal('50.00')
        }
    ]
    
    for program_data in programs:
        program, created = UniversityProgram.objects.get_or_create(
            name=program_data['name'],
            defaults=program_data
        )
        if created:
            print(f"✅ Created university program: {program.name}")
        else:
            print(f"⚠️ University program already exists: {program.name}")

def create_service_categories():
    """Create sample service categories"""
    categories = [
        {
            'name': 'General Consultation',
            'category_type': 'consultation',
            'description': 'Basic medical consultation with healthcare provider',
            'base_price': Decimal('150.00'),
            'student_price': Decimal('75.00')
        },
        {
            'name': 'Emergency Care',
            'category_type': 'emergency',
            'description': 'Emergency medical treatment and care',
            'base_price': Decimal('500.00'),
            'student_price': Decimal('200.00')
        },
        {
            'name': 'Blood Test',
            'category_type': 'laboratory',
            'description': 'Complete blood count and basic metabolic panel',
            'base_price': Decimal('120.00'),
            'student_price': Decimal('40.00')
        },
        {
            'name': 'X-Ray',
            'category_type': 'procedure',
            'description': 'Digital X-ray imaging',
            'base_price': Decimal('200.00'),
            'student_price': Decimal('80.00')
        },
        {
            'name': 'Prescription Medication',
            'category_type': 'pharmacy',
            'description': 'Prescribed medications from campus pharmacy',
            'base_price': Decimal('50.00'),
            'student_price': Decimal('25.00')
        },
        {
            'name': 'Annual Health Check',
            'category_type': 'health_check',
            'description': 'Comprehensive annual health examination',
            'base_price': Decimal('300.00'),
            'student_price': Decimal('100.00')
        },
        {
            'name': 'Mental Health Counseling',
            'category_type': 'mental_health',
            'description': 'Individual counseling session',
            'base_price': Decimal('180.00'),
            'student_price': Decimal('60.00')
        },
        {
            'name': 'Vaccination',
            'category_type': 'vaccination',
            'description': 'Immunization and vaccination services',
            'base_price': Decimal('80.00'),
            'student_price': Decimal('30.00')
        }
    ]
    
    for category_data in categories:
        category, created = ServiceCategory.objects.get_or_create(
            name=category_data['name'],
            defaults=category_data
        )
        if created:
            print(f"✅ Created service category: {category.name}")
        else:
            print(f"⚠️ Service category already exists: {category.name}")

def create_sample_insurance():
    """Create sample insurance records for existing patients"""
    try:
        patients = Patient.objects.all()[:5]  # Get first 5 patients
        
        insurance_types = [
            ('university', 'University Health Plan', 80.00, 500.00),
            ('private', 'Blue Cross Blue Shield', 75.00, 1000.00),
            ('government', 'Medicaid', 90.00, 0.00),
            ('university', 'University Health Plan', 80.00, 500.00),
            ('private', 'Aetna', 70.00, 750.00)
        ]
        
        for i, patient in enumerate(patients):
            if i < len(insurance_types):
                insurance_type, provider, coverage, deductible = insurance_types[i]
                
                insurance, created = StudentInsurance.objects.get_or_create(
                    student=patient,
                    defaults={
                        'insurance_type': insurance_type,
                        'insurance_provider': provider,
                        'coverage_percentage': Decimal(str(coverage)),
                        'deductible_remaining': Decimal(str(deductible)),
                        'is_verified': True,
                        'verified_until': date.today() + timedelta(days=365)
                    }
                )
                if created:
                    print(f"✅ Created insurance for patient: {patient.user.get_full_name()}")
                else:
                    print(f"⚠️ Insurance already exists for patient: {patient.user.get_full_name()}")
    
    except Exception as e:
        print(f"❌ Error creating sample insurance: {e}")

def create_sample_invoices():
    """Create sample invoices"""
    try:
        patients = Patient.objects.all()[:3]  # Get first 3 patients
        consultation = ServiceCategory.objects.get(name='General Consultation')
        blood_test = ServiceCategory.objects.get(name='Blood Test')
        
        for i, patient in enumerate(patients):
            # Create invoice
            invoice = Invoice.objects.create(
                student=patient,
                service_description=f"Medical consultation and lab work for {patient.user.get_full_name()}",
                due_date=date.today() + timedelta(days=30),
                semester="Fall 2024",
                academic_year="2024-2025"
            )
            
            # Add consultation item
            InvoiceItem.objects.create(
                invoice=invoice,
                service_category=consultation,
                description="General medical consultation",
                quantity=1,
                unit_price=consultation.student_price
            )
            
            # Add lab test item
            InvoiceItem.objects.create(
                invoice=invoice,
                service_category=blood_test,
                description="Complete blood count",
                quantity=1,
                unit_price=blood_test.student_price
            )
            
            # Apply insurance if available
            if hasattr(patient, 'insurance') and patient.insurance.is_verified:
                coverage_amount = invoice.subtotal * (patient.insurance.coverage_percentage / 100)
                invoice.insurance_coverage = coverage_amount
                invoice.save()
            
            print(f"✅ Created invoice for patient: {patient.user.get_full_name()}")
    
    except Exception as e:
        print(f"❌ Error creating sample invoices: {e}")

def create_sample_payments():
    """Create sample payments for some invoices"""
    try:
        invoices = Invoice.objects.filter(balance_due__gt=0)[:2]
        
        for invoice in invoices:
            payment_amount = invoice.balance_due / 2  # Pay half
            
            payment = Payment.objects.create(
                invoice=invoice,
                amount=payment_amount,
                payment_method='card',
                status='completed',
                transaction_id=f"TXN{invoice.id}001"
            )
            
            print(f"✅ Created payment for invoice: {invoice.invoice_number}")
    
    except Exception as e:
        print(f"❌ Error creating sample payments: {e}")

def create_sample_fee_waiver():
    """Create a sample fee waiver request"""
    try:
        invoice = Invoice.objects.filter(balance_due__gt=0).first()
        
        if invoice:
            waiver = FeeWaiver.objects.create(
                student=invoice.student,
                invoice=invoice,
                waiver_type='financial_hardship',
                reason='Student experiencing financial difficulties due to family emergency',
                requested_amount=invoice.balance_due / 2,
                status='pending'
            )
            
            print(f"✅ Created fee waiver request for invoice: {invoice.invoice_number}")
    
    except Exception as e:
        print(f"❌ Error creating sample fee waiver: {e}")

def main():
    """Main setup function"""
    print("🏥 Setting up billing system data...")
    print("=" * 50)
    
    try:
        create_university_programs()
        print()
        
        create_service_categories()
        print()
        
        create_sample_insurance()
        print()
        
        create_sample_invoices()
        print()
        
        create_sample_payments()
        print()
        
        create_sample_fee_waiver()
        print()
        
        print("=" * 50)
        print("✅ Billing system setup completed successfully!")
        print("\nSummary:")
        print(f"- University Programs: {UniversityProgram.objects.count()}")
        print(f"- Service Categories: {ServiceCategory.objects.count()}")
        print(f"- Student Insurance: {StudentInsurance.objects.count()}")
        print(f"- Invoices: {Invoice.objects.count()}")
        print(f"- Payments: {Payment.objects.count()}")
        print(f"- Fee Waivers: {FeeWaiver.objects.count()}")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()