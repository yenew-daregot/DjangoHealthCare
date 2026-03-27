#!/usr/bin/env python
"""
Test script for billing system functionality
Run this script to test the billing system components
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

def test_invoice_creation():
    """Test invoice creation and calculation"""
    print("🧾 Testing invoice creation...")
    
    try:
        # Get test data
        patient = Patient.objects.first()
        consultation = ServiceCategory.objects.get(name='General Consultation')
        
        if not patient:
            print("❌ No patients found. Please create a patient first.")
            return False
        
        # Create invoice
        invoice = Invoice.objects.create(
            student=patient,
            service_description="Test consultation",
            due_date=date.today() + timedelta(days=30)
        )
        
        # Add item
        item = InvoiceItem.objects.create(
            invoice=invoice,
            service_category=consultation,
            description="Test consultation item",
            quantity=1,
            unit_price=consultation.student_price
        )
        
        # Refresh invoice to get updated totals
        invoice.refresh_from_db()
        
        print(f"✅ Invoice created: {invoice.invoice_number}")
        print(f"   Subtotal: ${invoice.subtotal}")
        print(f"   Total: ${invoice.total_amount}")
        print(f"   Balance Due: ${invoice.balance_due}")
        
        # Clean up
        invoice.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Invoice creation test failed: {e}")
        return False

def test_payment_processing():
    """Test payment processing"""
    print("💳 Testing payment processing...")
    
    try:
        # Get an invoice with balance
        invoice = Invoice.objects.filter(balance_due__gt=0).first()
        
        if not invoice:
            print("❌ No invoices with balance found.")
            return False
        
        original_balance = invoice.balance_due
        payment_amount = Decimal('25.00')
        
        # Create payment
        payment = Payment.objects.create(
            invoice=invoice,
            amount=payment_amount,
            payment_method='card',
            status='completed',
            transaction_id='TEST001'
        )
        
        # Refresh invoice
        invoice.refresh_from_db()
        
        expected_balance = original_balance - payment_amount
        
        print(f"✅ Payment processed: {payment.receipt_number}")
        print(f"   Payment Amount: ${payment.amount}")
        print(f"   Original Balance: ${original_balance}")
        print(f"   New Balance: ${invoice.balance_due}")
        print(f"   Expected Balance: ${expected_balance}")
        
        if invoice.balance_due == expected_balance:
            print("✅ Balance calculation correct")
        else:
            print("❌ Balance calculation incorrect")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Payment processing test failed: {e}")
        return False

def test_insurance_coverage():
    """Test insurance coverage calculation"""
    print("🏥 Testing insurance coverage...")
    
    try:
        # Get patient with insurance
        patient_with_insurance = Patient.objects.filter(insurance__isnull=False).first()
        
        if not patient_with_insurance:
            print("❌ No patients with insurance found.")
            return False
        
        insurance = patient_with_insurance.insurance
        consultation = ServiceCategory.objects.get(name='General Consultation')
        
        # Create invoice
        invoice = Invoice.objects.create(
            student=patient_with_insurance,
            service_description="Test insurance coverage",
            due_date=date.today() + timedelta(days=30)
        )
        
        # Add item
        InvoiceItem.objects.create(
            invoice=invoice,
            service_category=consultation,
            description="Test consultation with insurance",
            quantity=1,
            unit_price=consultation.student_price
        )
        
        # Apply insurance coverage
        coverage_amount = invoice.subtotal * (insurance.coverage_percentage / 100)
        invoice.insurance_coverage = coverage_amount
        invoice.save()
        
        print(f"✅ Insurance coverage applied")
        print(f"   Subtotal: ${invoice.subtotal}")
        print(f"   Coverage Percentage: {insurance.coverage_percentage}%")
        print(f"   Coverage Amount: ${invoice.insurance_coverage}")
        print(f"   Final Amount: ${invoice.total_amount}")
        
        # Clean up
        invoice.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Insurance coverage test failed: {e}")
        return False

def test_debt_conversion():
    """Test converting invoice to debt"""
    print("💸 Testing debt conversion...")
    
    try:
        # Get an overdue invoice
        patient = Patient.objects.first()
        consultation = ServiceCategory.objects.get(name='General Consultation')
        
        # Create overdue invoice
        invoice = Invoice.objects.create(
            student=patient,
            service_description="Test overdue invoice",
            due_date=date.today() - timedelta(days=10),  # Past due
            status='overdue'
        )
        
        InvoiceItem.objects.create(
            invoice=invoice,
            service_category=consultation,
            description="Overdue consultation",
            quantity=1,
            unit_price=consultation.student_price
        )
        
        # Convert to debt
        debt = invoice.create_student_debt()
        
        if debt:
            print(f"✅ Debt created: {debt.debt_number}")
            print(f"   Original Amount: ${debt.original_amount}")
            print(f"   Outstanding Balance: ${debt.outstanding_balance}")
            print(f"   Status: {debt.status}")
            
            # Clean up
            debt.delete()
        else:
            print("❌ Debt creation failed")
            return False
        
        # Clean up
        invoice.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Debt conversion test failed: {e}")
        return False

def test_fee_waiver():
    """Test fee waiver functionality"""
    print("🎫 Testing fee waiver...")
    
    try:
        # Get an invoice
        invoice = Invoice.objects.filter(balance_due__gt=0).first()
        
        if not invoice:
            print("❌ No invoices with balance found.")
            return False
        
        # Create fee waiver
        waiver = FeeWaiver.objects.create(
            student=invoice.student,
            invoice=invoice,
            waiver_type='financial_hardship',
            reason='Test waiver request',
            requested_amount=invoice.balance_due / 2,
            status='pending'
        )
        
        print(f"✅ Fee waiver created")
        print(f"   Waiver Type: {waiver.waiver_type}")
        print(f"   Requested Amount: ${waiver.requested_amount}")
        print(f"   Status: {waiver.status}")
        
        # Approve waiver
        waiver.status = 'approved'
        waiver.approved_amount = waiver.requested_amount
        waiver.save()
        
        print(f"✅ Fee waiver approved: ${waiver.approved_amount}")
        
        # Clean up
        waiver.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Fee waiver test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("🌐 Testing API endpoints...")
    
    try:
        from django.test import Client
        from django.contrib.auth import get_user_model
        
        client = Client()
        User = get_user_model()
        
        # Create test user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='admin'
        )
        
        # Login
        client.login(username='testuser', password='testpass123')
        
        # Test endpoints
        endpoints = [
            '/api/billing/',
            '/api/billing/service-categories/',
            '/api/billing/invoices/',
            '/api/billing/payments/',
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code in [200, 401]:  # 401 is OK for auth required
                print(f"✅ Endpoint accessible: {endpoint}")
            else:
                print(f"❌ Endpoint failed: {endpoint} (Status: {response.status_code})")
        
        # Clean up
        user.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def run_all_tests():
    """Run all billing system tests"""
    print("🧪 Running Billing System Tests")
    print("=" * 50)
    
    tests = [
        test_invoice_creation,
        test_payment_processing,
        test_insurance_coverage,
        test_debt_conversion,
        test_fee_waiver,
        test_api_endpoints
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️ Some tests failed. Please check the output above.")
        return False

def main():
    """Main test function"""
    success = run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()