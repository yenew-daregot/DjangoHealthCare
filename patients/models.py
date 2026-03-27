from django.db import models
from users.models import CustomUser
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator  
from decimal import Decimal  
import re

class Patient(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='patient_profile',
        limit_choices_to={'role': 'PATIENT'}
    )
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    
    #Use validators for height and weight
    height = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="Height in cm",
        validators=[
            MinValueValidator(Decimal('50.0'), message="Height must be at least 50.0 cm."),
            MaxValueValidator(Decimal('250.0'), message="Height cannot exceed 250.0 cm.")
        ]
    )
    
    weight = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        help_text="Weight in kg",
        validators=[
            MinValueValidator(Decimal('2.0'), message="Weight must be at least 2.0 kg."),
            MaxValueValidator(Decimal('300.0'), message="Weight cannot exceed 300.0 kg.")
        ]
    )
    
    emergency_contact = models.CharField(max_length=100, blank=True, help_text="Emergency contact name")
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    insurance_id = models.CharField(max_length=50, blank=True)
    allergy_notes = models.TextField(blank=True) 
    chronic_conditions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        """
        Custom validation for Patient model
        """
        super().clean()
        
        # Validate user role
        if self.user.role != 'PATIENT': 
            raise ValidationError({'user': 'Only users with PATIENT role can be assigned as patients.'})
        
        # Validate age and date_of_birth consistency
        if self.date_of_birth:
            calculated_age = self.calculate_age(self.date_of_birth)
            if self.age and self.age != calculated_age:
                raise ValidationError({
                    'age': f'Age should be {calculated_age} based on date of birth {self.date_of_birth}.'
                })
            
            # Auto-calculate age
            if not self.age:
                self.age = calculated_age
        
        # Validate emergency contact phone format
        if self.emergency_contact_phone:
            if not re.match(r'^\+?1?\d{9,15}$', self.emergency_contact_phone):
                raise ValidationError({
                    'emergency_contact_phone': 'Enter a valid phone number.'
                })

    def calculate_age(self, birth_date):
        """Calculate age from date of birth"""
        today = timezone.now().date()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Patient: {self.user.get_full_name() or self.user.username}"

    @property
    def bmi(self):
        """Calculate BMI if height and weight are available"""
        if self.height and self.weight:
            # Convert height from cm to meters
            height_in_meters = float(self.height) / 100
            bmi_value = float(self.weight) / (height_in_meters ** 2)
            return round(bmi_value, 1)
        return None

    @property
    def bmi_category(self):
        """Get BMI category"""
        bmi = self.bmi
        if not bmi:
            return None
            
        if bmi < 18.5:
            return "Underweight"
        elif 18.5 <= bmi < 25:
            return "Normal weight"
        elif 25 <= bmi < 30:
            return "Overweight"
        else:
            return "Obese"