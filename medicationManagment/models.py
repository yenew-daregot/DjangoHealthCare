from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
import json

class Medication(models.Model):
    FREQUENCY_CHOICES = [
        ('once', 'Once'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('as_needed', 'As Needed'),
    ]
    
    UNIT_CHOICES = [
        ('mg', 'mg'),
        ('ml', 'ml'),
        ('tablet', 'tablet'),
        ('capsule', 'capsule'),
        ('drops', 'drops'),
    ]

    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='medications')
    name = models.CharField(max_length=200)
    dosage = models.DecimalField(max_digits=6, decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    times_per_day = models.IntegerField(default=1)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    instructions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        """Validate medication data"""
        if self.dosage <= 0:
            raise ValidationError({'dosage': 'Dosage must be greater than zero'})
        
        if self.times_per_day <= 0:
            raise ValidationError({'times_per_day': 'Times per day must be greater than zero'})
        
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'End date cannot be before start date'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.patient.username}"

class MedicationSchedule(models.Model):
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='schedules')
    scheduled_time = models.TimeField()
    days_of_week = models.CharField(max_length=50, default='0,1,2,3,4,5,6')  # 0=Sunday, 6=Saturday
    is_active = models.BooleanField(default=True)

    def clean(self):
        """Validate days_of_week format"""
        try:
            days = [int(day.strip()) for day in self.days_of_week.split(',')]
            for day in days:
                if day < 0 or day > 6:
                    raise ValidationError({'days_of_week': 'Days must be between 0 (Sunday) and 6 (Saturday)'})
        except ValueError:
            raise ValidationError({'days_of_week': 'Invalid format. Use comma-separated numbers (0-6)'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.medication.name} at {self.scheduled_time}"

class MedicationDose(models.Model):
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='doses')
    scheduled_time = models.DateTimeField()
    taken_time = models.DateTimeField(null=True, blank=True)
    is_taken = models.BooleanField(default=False)
    is_skipped = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-scheduled_time']
        indexes = [
            models.Index(fields=['medication', 'scheduled_time']),
            models.Index(fields=['scheduled_time', 'is_taken']),
        ]

    def clean(self):
        """Validate dose data"""
        if self.is_taken and self.is_skipped:
            raise ValidationError('Dose cannot be both taken and skipped')
        
        if self.is_taken and not self.taken_time:
            raise ValidationError({'taken_time': 'Taken time is required when marking dose as taken'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        status = "Taken" if self.is_taken else "Skipped" if self.is_skipped else "Pending"
        return f"{self.medication.name} - {self.scheduled_time} ({status})"

class MedicationReminder(models.Model):
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='reminders')
    reminder_time = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['reminder_time']
        indexes = [
            models.Index(fields=['reminder_time', 'is_sent']),
        ]

    def __str__(self):
        return f"Reminder for {self.medication.name} at {self.reminder_time}"