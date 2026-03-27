from django.db import models
from django.utils import timezone

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    )
    TYPE_CHOICES = (
        ('consultation', 'Consultation'),
        ('follow_up', 'Follow-up'),
        ('emergency', 'Emergency'),
        ('vaccination', 'Vaccination'),
        ('checkup', 'Routine Checkup'),
        ('sick_visit', 'Sick Visit'),
        ('second_opinion', 'Second Opinion'),  
        ('prescription_renewal', 'Prescription Renewal'),
    )
    
    # Basic Information
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='appointments')
    appointment_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Timing
    appointment_date = models.DateTimeField()
    duration = models.IntegerField(default=30)  # in minutes
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    
    # Medical Information
    appointment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='consultation')
    reason = models.TextField()
    symptoms = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=(
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('emergency', 'Emergency'),
    ), default='medium')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Administrative
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, related_name='created_appointments')
    notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['appointment_date']
        indexes = [
            models.Index(fields=['appointment_date', 'status']),
            models.Index(fields=['patient', 'appointment_date']),
            models.Index(fields=['doctor', 'appointment_date']),
        ]
    
    def __str__(self):
        return f"Appointment: {self.appointment_number} - {self.patient} with {self.doctor}"
    
    def save(self, *args, **kwargs):
        if not self.appointment_number:
            self.appointment_number = self.generate_appointment_number()
        
        # Auto-set actual times based on status
        if self.status == 'in_progress' and not self.actual_start_time:
            self.actual_start_time = timezone.now()
        elif self.status == 'completed' and not self.actual_end_time:
            self.actual_end_time = timezone.now()
        
        super().save(*args, **kwargs)
    
    def generate_appointment_number(self):
        """Generate unique appointment number"""
        import random
        import string
        timestamp = timezone.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"APT-{timestamp}-{random_str}"
    
    @property
    def is_past_due(self):
        """Check if appointment is past its scheduled time"""
        return self.appointment_date < timezone.now() and self.status in ['scheduled', 'confirmed']
    
    @property
    def duration_minutes(self):
        """Calculate actual duration in minutes"""
        if self.actual_start_time and self.actual_end_time:
            return (self.actual_end_time - self.actual_start_time).total_seconds() / 60
        return None

class AppointmentSlot(models.Model):
    """Model to manage available appointment slots for doctors"""
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='slots')
    slot_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    max_patients = models.IntegerField(default=1)
    current_bookings = models.IntegerField(default=0)
    class Meta:
        unique_together = ['doctor', 'slot_date', 'start_time']
        ordering = ['slot_date', 'start_time']
    
    def __str__(self):
        return f"{self.doctor.user.get_full_name()} - {self.slot_date} {self.start_time}"
    
    @property
    def is_fully_booked(self):
        return self.current_bookings >= self.max_patients

class AppointmentReminder(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=(
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ))
    scheduled_time = models.DateTimeField()
    sent_time = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['scheduled_time']