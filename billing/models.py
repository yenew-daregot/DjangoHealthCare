from django.db import models
from datetime import timedelta
from django.utils import timezone
import random
import string
from patients.models import Patient
from appointments.models import Appointment
from labs.models import LabRequest
from django.contrib.auth import get_user_model

User = get_user_model()


class UniversityProgram(models.Model):
    PROGRAM_TYPES = (
        ('undergraduate', 'Undergraduate'),
        ('graduate', 'Graduate'),
        ('phd', 'PhD'),
        ('international', 'International Student'),
        ('exchange', 'Exchange Student'),
    )
    
    name = models.CharField(max_length=100)
    program_type = models.CharField(max_length=20, choices=PROGRAM_TYPES)
    department = models.CharField(max_length=100)
    tuition_coverage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.department}"
    
    class Meta:
        ordering = ['name']


class StudentInsurance(models.Model):
    INSURANCE_TYPES = (
        ('university', 'University Health Plan'),
        ('private', 'Private Insurance'),
        ('government', 'Government Plan'),
        ('none', 'No Insurance'),
    )
    
    student = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='insurance')
    insurance_type = models.CharField(max_length=20, choices=INSURANCE_TYPES, default='university')
    policy_number = models.CharField(max_length=50, blank=True)
    insurance_provider = models.CharField(max_length=100, blank=True)
    coverage_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=80.00)
    deductible_remaining = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    verified_until = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Student Insurances"
        ordering = ['-is_verified', 'student']
    
    def __str__(self):
        return f"{self.student} - {self.insurance_type}"


class ServiceCategory(models.Model):
    CATEGORY_TYPES = (
        ('consultation', 'Doctor Consultation'),
        ('emergency', 'Emergency Care'),
        ('laboratory', 'Laboratory Tests'),
        ('pharmacy', 'Pharmacy'),
        ('procedure', 'Medical Procedure'),
        ('vaccination', 'Vaccination'),
        ('health_check', 'Health Check-up'),
        ('mental_health', 'Mental Health Services'),
    )
    
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    student_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Service Categories"
        ordering = ['category_type', 'name']
    
    def __str__(self):
        return f"{self.name} - ${self.student_price}"


class Invoice(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('sent', 'Sent to Student'),
        ('pending_insurance', 'Pending Insurance'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
        ('waived', 'Waived'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('student_account', 'Student Account'),
        ('insurance', 'Insurance'),
        ('bank_transfer', 'Bank Transfer'),
        ('waiver', 'Fee Waiver'),
    )
    
    # Basic Information
    invoice_number = models.CharField(max_length=50, unique=True)
    student = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='invoices')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    lab_request = models.ForeignKey(LabRequest, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Service Information
    service_description = models.TextField()
    
    # Dates
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Amount Calculations
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    university_subsidy = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    insurance_coverage = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    student_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    balance_due = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)
    
    # Academic Information
    semester = models.CharField(max_length=50, blank=True)
    academic_year = models.CharField(max_length=20, blank=True)
    
    # Administrative
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issue_date', '-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['due_date', 'status']),
        ]
    
    def __str__(self):
        return f"Invoice: {self.invoice_number} - {self.student}"
    
    def save(self, *args, **kwargs):
        # Calculate balance before saving
        self.balance_due = max(self.total_amount - self.amount_paid, 0)
        
        # Auto-update status based on payment
        if self.amount_paid >= self.total_amount and self.total_amount > 0:
            self.status = 'paid'
            if not self.payment_date:
                self.payment_date = timezone.now()
        elif self.amount_paid > 0:
            self.status = 'partially_paid'
        
        # Mark as overdue if past due date
        if (self.due_date < timezone.now().date() and 
            self.balance_due > 0 and 
            self.status not in ['paid', 'waived', 'cancelled']):
            self.status = 'overdue'
        
        super().save(*args, **kwargs)
    
    def create_student_debt(self):
        """Convert unpaid invoice to student debt"""
        if self.balance_due > 0 and self.status in ['overdue', 'sent']:
            debt_number = f"DEBT{self.invoice_number}"
            
            debt, created = StudentDebt.objects.get_or_create(
                debt_number=debt_number,
                defaults={
                    'student': self.student,
                    'academic_year': self.academic_year,
                    'semester': self.semester,
                    'original_amount': self.balance_due,
                    'outstanding_balance': self.balance_due,
                    'incurred_date': self.issue_date,
                    'due_date': self.due_date + timedelta(days=30),
                    'description': f"Medical services: {self.service_description[:100]}",
                    'notes': f"Converted from invoice {self.invoice_number}",
                    'status': 'overdue' if self.status == 'overdue' else 'active'
                }
            )
            return debt
        return None


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    service_category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT)
    description = models.TextField()
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    
    class Meta:
        ordering = ['id']
    
    def save(self, *args, **kwargs):
        # Calculate total price with discount
        discount_amount = (self.unit_price * self.discount_percentage) / 100
        discounted_price = self.unit_price - discount_amount
        self.total_price = discounted_price * self.quantity
        super().save(*args, **kwargs)
        
        # Update invoice totals
        self.update_invoice_totals()
    
    def update_invoice_totals(self):
        invoice = self.invoice
        invoice.subtotal = sum(item.total_price for item in invoice.items.all())
        invoice.total_amount = invoice.subtotal - invoice.university_subsidy - invoice.insurance_coverage - invoice.student_discount
        invoice.save()
    
    def __str__(self):
        return f"{self.service_category.name} x{self.quantity}"


class StudentDebt(models.Model):
    DEBT_STATUS_CHOICES = (
        ('active', 'Active'),
        ('pending_verification', 'Pending Verification'),
        ('payment_plan', 'Payment Plan'),
        ('overdue', 'Overdue'),
        ('in_collections', 'In Collections'),
        ('cleared', 'Cleared'),
        ('waived', 'Waived'),
    )
    
    # Student Information
    student = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='debts')
    academic_year = models.CharField(max_length=20, blank=True)
    semester = models.CharField(max_length=50, blank=True)
    
    # Debt Information
    debt_number = models.CharField(max_length=50, unique=True)
    original_amount =models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    outstanding_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Dates
    incurred_date = models.DateField()
    due_date = models.DateField()
    last_payment_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=25, choices=DEBT_STATUS_CHOICES, default='active')
    is_urgent = models.BooleanField(default=False)
    
    # Administrative
    description = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-incurred_date', '-created_at']
        indexes = [
            models.Index(fields=['debt_number']),
            models.Index(fields=['student', 'status']),
            models.Index(fields=['due_date', 'status']),
        ]
    
    def __str__(self):
        return f"Debt: {self.debt_number} - {self.student} - ${self.outstanding_balance}"
    
    def save(self, *args, **kwargs):
        # Auto-set urgent if overdue
        if self.due_date < timezone.now().date() and self.status in ['active', 'pending_verification']:
            self.is_urgent = True
            self.status = 'overdue'
        
        # Auto-calculate outstanding balance if not set
        if not self.outstanding_balance:
            self.outstanding_balance = self.original_amount
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.outstanding_balance > 0
    
    @property
    def days_overdue(self):
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    )
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    student_debt = models.ForeignKey(StudentDebt, on_delete=models.CASCADE, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=Invoice.PAYMENT_METHOD_CHOICES)
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    receipt_number = models.CharField(max_length=50, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment: ${self.amount} - {self.receipt_number}"
    
    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.receipt_number:
            # Generate receipt number
            date_str = timezone.now().strftime('%Y%m%d')
            random_num = ''.join(random.choices(string.digits, k=4))
            self.receipt_number = f"RCP{date_str}{random_num}"
            
            # Update invoice if exists
            if self.invoice:
                self.invoice.amount_paid = self.invoice.amount_paid + self.amount
                self.invoice.payment_date = self.payment_date
                self.invoice.payment_method = self.payment_method
                self.invoice.save()
            
            # Update student_debt if exists
            if self.student_debt:
                self.student_debt.outstanding_balance = max(0, self.student_debt.outstanding_balance - self.amount)
                self.student_debt.last_payment_date = self.payment_date.date()
                if self.student_debt.outstanding_balance <= 0:
                    self.student_debt.status = 'cleared'
                self.student_debt.save()
        
        super().save(*args, **kwargs)


class FeeWaiver(models.Model):
    WAIVER_TYPES = (
        ('financial_hardship', 'Financial Hardship'),
        ('academic_scholarship', 'Academic Scholarship'),
        ('athletic_scholarship', 'Athletic Scholarship'),
        ('international_student', 'International Student Support'),
        ('emergency', 'Emergency Situation'),
        ('university_fund', 'University Fund'),
        ('other', 'Other'),
    )
    
    student = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='waivers')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, null=True, blank=True)
    student_debt = models.ForeignKey(StudentDebt, on_delete=models.CASCADE, null=True, blank=True)
    waiver_type = models.CharField(max_length=30, choices=WAIVER_TYPES)
    reason = models.TextField()
    requested_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    approved_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_waivers')
    approved_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=(
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('partially_approved', 'Partially Approved'),
    ), default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Waiver: {self.waiver_type} - ${self.approved_amount}"
    
    def save(self, *args, **kwargs):
        if self.status == 'approved' and self.approved_amount > 0:
            if not self.approved_date:
                self.approved_date = timezone.now()
            
            # Apply waiver to invoice or debt
            if self.invoice:
                self.invoice.university_subsidy += self.approved_amount
                self.invoice.status = 'waived'
                self.invoice.save()
            
            if self.student_debt:
                self.student_debt.outstanding_balance -= self.approved_amount
                self.student_debt.status = 'waived'
                self.student_debt.save()
        
        super().save(*args, **kwargs)


class PaymentPlan(models.Model):
    student_debt = models.ForeignKey(StudentDebt, on_delete=models.CASCADE, related_name='payment_plans')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    number_of_installments = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=(
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('defaulted', 'Defaulted'),
    ), default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment Plan: {self.student_debt} - ${self.installment_amount}/month"