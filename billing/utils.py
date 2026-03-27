from django.utils import timezone
import random
import string


def generate_invoice_number():
    """Generate unique invoice number"""
    timestamp = timezone.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.digits, k=6))
    return f"INV-{timestamp}-{random_str}"


def generate_debt_number():
    """Generate unique debt number"""
    timestamp = timezone.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.digits, k=6))
    return f"DEBT-{timestamp}-{random_str}"


def calculate_student_discount(student, service_category):
    """Calculate student discount based on program and insurance"""
    discount = service_category.base_price - service_category.student_price
    
    # Additional discount logic can be added here
    return discount


def calculate_insurance_coverage(student, amount):
    """Calculate insurance coverage amount"""
    if hasattr(student, 'insurance') and student.insurance.is_verified:
        insurance = student.insurance
        coverage_amount = amount * (insurance.coverage_percentage / 100)
        
        # Apply deductible
        if insurance.deductible_remaining > 0:
            deductible_applied = min(coverage_amount, insurance.deductible_remaining)
            coverage_amount -= deductible_applied
            insurance.deductible_remaining -= deductible_applied
            insurance.save()
        
        return coverage_amount
    return 0