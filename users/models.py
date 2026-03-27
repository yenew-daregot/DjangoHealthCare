from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
import re

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        
        ('PATIENT', 'Patient'),
        ('DOCTOR', 'Doctor'),
        ('LABORATORIST', 'Laboratorist'),
        ('ADMIN', 'Admin'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PATIENT')
    phone_number = models.CharField(max_length=15, blank=True)
    avatar_url = models.CharField(max_length=255, blank=True)
    fcm_token = models.TextField(blank=True, help_text='Firebase Cloud Messaging token for push notifications')
    
    reset_token = models.CharField(max_length=100, blank=True, null=True)
    reset_token_created = models.DateTimeField(blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        
        # Phone number validation 
        if self.phone_number:
            # Remove any spaces, dashes, parentheses for validation
            cleaned_phone = re.sub(r'[\s\-\(\)]', '', self.phone_number)
            
            # Allow + at the beginning for international format
            if cleaned_phone.startswith('+'):
                cleaned_phone = cleaned_phone[1:]  # Remove + for digit check
            
            # Check if it contains only digits and has reasonable length
            if not cleaned_phone.isdigit():
                raise ValidationError({'phone_number': 'Phone number should contain only digits, spaces, dashes, parentheses, or + at the beginning.'})
            
            if len(cleaned_phone) < 10:
                raise ValidationError({'phone_number': 'Phone number should be at least 10 digits long.'})
            
            # Keep the original format (don't modify the phone_number)
            # self.phone_number = cleaned_phone  # Commented out to preserve original format
            
        #Ensure ADMIN users have is_staff=True
        if self.role == 'ADMIN':
            self.is_staff = True
            #give superuser privileges for full access
            self.is_superuser = True  

    def save(self, *args, **kwargs):
        # Ensure is_staff is set before saving for ADMIN users
        if self.role == 'ADMIN' and not self.is_staff:
            self.is_staff = True
        if self.role == 'ADMIN' and not self.is_superuser:
            self.is_superuser = True
            
        self.full_clean()  
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email} ({self.role})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name