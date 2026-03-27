from django.db import models
from patients.models import Patient
from doctors.models import Doctor
from django.contrib.auth import get_user_model

User = get_user_model()

class LabTest(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    normal_range = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    category = models.CharField(max_length=100, blank=True)
    sample_type = models.CharField(max_length=100, blank=True)  
    preparation_instructions = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class LabRequest(models.Model):
    TEST_STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('assigned', 'Assigned to Lab'),
        ('sample_collected', 'Sample Collected'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    test = models.ForeignKey(LabTest, on_delete=models.CASCADE)
    laboratorist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    requested_date = models.DateTimeField(auto_now_add=True)
    assigned_date = models.DateTimeField(null=True, blank=True)
    sample_collected_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=TEST_STATUS_CHOICES, default='requested')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    clinical_notes = models.TextField(blank=True, help_text="Doctor's clinical notes")
    lab_notes = models.TextField(blank=True, help_text="Laboratorist's notes")
    
    # Request document (doctor can upload prescription/request form)
    request_document = models.FileField(upload_to='lab_requests/', null=True, blank=True)
    
    def __str__(self):
        return f"Lab: {self.test.name} for {self.patient}"

class LabResult(models.Model):
    lab_request = models.OneToOneField(LabRequest, on_delete=models.CASCADE, related_name='result')
    
    # Text results
    result_text = models.TextField(blank=True)
    
    # File uploads (PDF reports, images, etc.)
    result_document = models.FileField(upload_to='lab_results/', null=True, blank=True)
    
    # Structured results for common tests
    result_values = models.JSONField(default=dict, blank=True)  # For structured data
    
    # Result interpretation
    interpretation = models.TextField(blank=True)
    is_abnormal = models.BooleanField(default=False)
    
    # Metadata
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Result for {self.lab_request}"