from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time, timedelta
import uuid
import json

User = get_user_model()

class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Doctor(models.Model):
    doctor_id = models.CharField(
        max_length=15,
        unique=True,
        editable=False,
        verbose_name="Doctor ID",
        db_index=True,  
        default='TEMP-ID'
    )
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='doctor_profile'
    )
    
    specialization = models.ForeignKey(
        Specialization, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    license_number = models.CharField(max_length=50, unique=True)
    qualification = models.TextField()
    years_of_experience = models.IntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_available = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    bio = models.TextField(blank=True)
    address = models.TextField(blank=True)
    consultation_hours = models.JSONField(default=dict, blank=True)  
    profile_picture = models.ImageField(upload_to='doctors/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    reviews_count = models.IntegerField(default=0)

    def __str__(self):
        doctor_id_display = self.doctor_id or "NO-ID"
        return f"{doctor_id_display} - Dr. {self.user.get_full_name()} - {self.specialization.name if self.specialization else 'General'}"

    @property
    def full_name(self):
        """Get doctor's full name from user"""
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}"
        return "Unknown Doctor"

    @property
    def email(self):
        return self.user.email

    @property
    def phone_number(self):
        return self.user.phone_number

    def save(self, *args, **kwargs):
        # Only generate ID for new records
        is_new = not self.pk
        
        if is_new and not self.doctor_id:
            # Generate sequential ID for new doctors
            self._generate_sequential_id()
        elif not self.doctor_id or self.doctor_id == 'TEMP-ID':
            # Handle existing records with TEMP-ID or null
            self._generate_sequential_id()
        
        super().save(*args, **kwargs)
    
    def _generate_sequential_id(self):
        """Generate sequential doctor ID"""
        try:
            # Get the highest existing sequential number
            existing_ids = Doctor.objects.exclude(
                doctor_id__isnull=True
            ).exclude(
                doctor_id='TEMP-ID'
            ).values_list('doctor_id', flat=True)
            
            max_number = 0
            for doc_id in existing_ids:
                if doc_id and doc_id.startswith('DOC') and len(doc_id) == 8:
                    try:
                        num_str = doc_id[3:]
                        if num_str.isdigit():
                            num = int(num_str)
                            if num > max_number:
                                max_number = num
                    except ValueError:
                        continue
            
            new_number = max_number + 1
            self.doctor_id = f"DOC{new_number:05d}"
            
        except Exception as e:
            # Fallback using UUID
            self.doctor_id = f"DOC{uuid.uuid4().hex[:5].upper()}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Doctor"
        verbose_name_plural = "Doctors"


# Schedule Models
class DoctorSchedule(models.Model):
    """Doctor's weekly schedule template"""
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    break_start = models.TimeField(null=True, blank=True, help_text="Break/lunch start time")
    break_end = models.TimeField(null=True, blank=True, help_text="Break/lunch end time")
    slot_duration = models.IntegerField(default=30, help_text="Appointment slot duration in minutes")
    max_patients_per_slot = models.IntegerField(default=1)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['doctor', 'day_of_week', 'start_time']
        ordering = ['day_of_week', 'start_time']
    
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")
        
        if self.break_start and self.break_end:
            if self.break_start >= self.break_end:
                raise ValidationError("Break start time must be before break end time")
            if not (self.start_time <= self.break_start < self.break_end <= self.end_time):
                raise ValidationError("Break time must be within working hours")
    
    def __str__(self):
        day_name = dict(self.DAYS_OF_WEEK)[self.day_of_week]
        return f"Dr. {self.doctor.full_name} - {day_name} {self.start_time}-{self.end_time}"
    
    def get_available_slots(self, date=None):
        """Get available time slots for this schedule"""
        if not date:
            date = timezone.now().date()
        
        slots = []
        current_time = datetime.combine(date, self.start_time)
        end_time = datetime.combine(date, self.end_time)
        slot_delta = timedelta(minutes=self.slot_duration)
        
        # Handle break time
        break_start = None
        break_end = None
        if self.break_start and self.break_end:
            break_start = datetime.combine(date, self.break_start)
            break_end = datetime.combine(date, self.break_end)
        
        while current_time < end_time:
            slot_end = current_time + slot_delta
            
            # Skip if slot overlaps with break time
            if break_start and break_end:
                if not (slot_end <= break_start or current_time >= break_end):
                    current_time = slot_end
                    continue
            
            slots.append({
                'start_time': current_time.time(),
                'end_time': slot_end.time(),
                'available': True  # This would be checked against appointments
            })
            
            current_time = slot_end
        
        return slots


class ScheduleException(models.Model):
    """Exceptions to regular schedule (holidays, special hours, blocked time)"""
    EXCEPTION_TYPES = [
        ('holiday', 'Holiday'),
        ('blocked', 'Blocked Time'),
        ('special_hours', 'Special Hours'),
        ('emergency', 'Emergency Block'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedule_exceptions')
    date = models.DateField()
    exception_type = models.CharField(max_length=20, choices=EXCEPTION_TYPES)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_available = models.BooleanField(default=False, help_text="Is doctor available during this exception")
    reason = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['doctor', 'date', 'start_time']
        ordering = ['date', 'start_time']
    
    def clean(self):
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("Start time must be before end time")
    
    def __str__(self):
        return f"Dr. {self.doctor.full_name} - {self.date} ({self.exception_type})"


class DoctorAvailability(models.Model):
    """Real-time availability status"""
    doctor = models.OneToOneField(Doctor, on_delete=models.CASCADE, related_name='availability')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    status_message = models.CharField(max_length=100, blank=True)
    auto_accept_appointments = models.BooleanField(default=False)
    emergency_available = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        status = "Online" if self.is_online else "Offline"
        return f"Dr. {self.doctor.full_name} - {status}"
    
    class Meta:
        verbose_name_plural = "Doctor Availabilities"