from django.db import models
from appointments.models import Appointment
from patients.models import Patient
from doctors.models import Doctor
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid

class Medication(models.Model):
    MEDICATION_TYPES = (
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('syrup', 'Syrup'),
        ('injection', 'Injection'),
        ('cream', 'Cream'),
        ('drops', 'Drops'),
        ('inhaler', 'Inhaler'),
        ('other', 'Other'),
    )
    
    name = models.CharField(max_length=100)
    generic_name = models.CharField(max_length=100, blank=True)
    manufacturer = models.CharField(max_length=100, blank=True)
    medication_type = models.CharField(max_length=20, choices=MEDICATION_TYPES, default='tablet')
    strength = models.CharField(max_length=50, blank=True, help_text="e.g., 500mg, 10ml")
    description = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['name', 'strength']
    
    def __str__(self):
        return f"{self.name} {self.strength}" if self.strength else self.name

class Prescription(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    )
    
    FREQUENCY_CHOICES = (
        ('once_daily', 'Once Daily'),
        ('twice_daily', 'Twice Daily'),
        ('three_times_daily', 'Three Times Daily'),
        ('four_times_daily', 'Four Times Daily'),
        ('as_needed', 'As Needed'),
        ('before_meals', 'Before Meals'),
        ('after_meals', 'After Meals'),
        ('at_bedtime', 'At Bedtime'),
        ('custom', 'Custom'),
    )
    
    prescription_id = models.CharField(max_length=20, unique=True, blank=True)
    appointment = models.ForeignKey(
        Appointment, 
        on_delete=models.CASCADE,
        related_name='prescriptions' 
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        null=True,
        blank=True
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        null=True,
        blank=True
    )
    medication = models.ForeignKey(
        Medication, 
        on_delete=models.CASCADE,
        related_name='prescriptions' 
    )
    dosage = models.CharField(max_length=50, help_text="e.g., 1 tablet, 5ml")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    custom_frequency = models.CharField(max_length=100, blank=True, help_text="If frequency is custom")
    duration = models.CharField(max_length=50, help_text="e.g., 7 days, 2 weeks")
    duration_days = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in days")
    instructions = models.TextField(blank=True)
    notes = models.TextField(blank=True, help_text="Doctor's notes")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Dates
    prescribed_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    
    # Refill information
    refills_allowed = models.PositiveIntegerField(default=0)
    refills_remaining = models.PositiveIntegerField(default=0)
    
    # Tracking
    is_urgent = models.BooleanField(default=False)
    pharmacy_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-prescribed_date']
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['doctor', 'prescribed_date']),
            models.Index(fields=['prescription_id']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.prescription_id:
            self.prescription_id = self.generate_prescription_id()
        
        # Auto-set patient and doctor from appointment
        if self.appointment:
            self.patient = self.appointment.patient
            self.doctor = self.appointment.doctor
        
        # Calculate end date if duration_days is provided
        if self.duration_days and not self.end_date:
            self.end_date = self.start_date + timezone.timedelta(days=self.duration_days)
        
        # Set refills_remaining if not set
        if self.refills_remaining is None:
            self.refills_remaining = self.refills_allowed
        
        super().save(*args, **kwargs)
    
    def generate_prescription_id(self):
        """Generate unique prescription ID"""
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        return f"RX-{timestamp}-{str(uuid.uuid4())[:8].upper()}"
    
    def clean(self):
        # Validate that dosage, frequency, duration are not empty
        if not self.dosage.strip():
            raise ValidationError({'dosage': 'Dosage is required.'})
        if not self.frequency:
            raise ValidationError({'frequency': 'Frequency is required.'})
        if self.frequency == 'custom' and not self.custom_frequency.strip():
            raise ValidationError({'custom_frequency': 'Custom frequency is required when frequency is set to custom.'})
        if not self.duration.strip():
            raise ValidationError({'duration': 'Duration is required.'})
    
    @property
    def is_expired(self):
        """Check if prescription has expired"""
        if self.end_date:
            return timezone.now().date() > self.end_date
        return False
    
    @property
    def days_remaining(self):
        """Calculate days remaining for prescription"""
        if self.end_date:
            remaining = (self.end_date - timezone.now().date()).days
            return max(0, remaining)
        return None
    
    @property
    def frequency_display(self):
        """Get human-readable frequency"""
        if self.frequency == 'custom':
            return self.custom_frequency
        return dict(self.FREQUENCY_CHOICES).get(self.frequency, self.frequency)
    
    def __str__(self):
        return f"RX-{self.prescription_id}: {self.medication.name} for {self.patient.user.get_full_name()}"

class PrescriptionRefill(models.Model):
    STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('dispensed', 'Dispensed'),
    )
    
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='refills'
    )
    requested_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='prescription_refill_requests'
    )
    approved_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_prescription_refills'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)
    denial_reason = models.TextField(blank=True)
    
    requested_date = models.DateTimeField(auto_now_add=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    dispensed_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-requested_date']
    
    def __str__(self):
        return f"Refill for {self.prescription.prescription_id} - {self.status}"