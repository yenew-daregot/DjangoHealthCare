from django.db import models
from patients.models import Patient
from doctors.models import Doctor
from appointments.models import Appointment
from labs.models import LabRequest
from prescriptions.models import Prescription
from django.core.exceptions import ValidationError
from django.utils import timezone

class MedicalRecord(models.Model):
    RECORD_TYPE_CHOICES = (
        ('consultation', 'Consultation Notes'),
        ('lab_result', 'Laboratory Result'),
        ('imaging', 'Imaging Report'),
        ('surgery', 'Surgical Report'),
        ('vaccination', 'Vaccination Record'),
        ('allergy', 'Allergy Information'),
        ('medication', 'Medication History'),
        ('vital_signs', 'Vital Signs'),
        ('diagnosis', 'Diagnosis'),
        ('treatment_plan', 'Treatment Plan'),
        ('progress_note', 'Progress Note'),
        ('discharge_summary', 'Discharge Summary'),
        ('emergency', 'Emergency Visit'),
        ('other', 'Other'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    # Basic Information
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='medical_records')
    record_type = models.CharField(max_length=20, choices=RECORD_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    clinical_notes = models.TextField(blank=True)
    
    # Dates
    date_recorded = models.DateTimeField()
    date_effective = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Related Records
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='medical_records')
    lab_request = models.ForeignKey(LabRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='medical_records')
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True, related_name='medical_records')
    
    # Files and Attachments
    file = models.FileField(upload_to='medical_records/%Y/%m/%d/', null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.IntegerField(null=True, blank=True)
    
    # Medical Information
    diagnosis_codes = models.JSONField(default=list, blank=True)  # ICD-10 codes
    procedure_codes = models.JSONField(default=list, blank=True)  # CPT codes
    symptoms = models.JSONField(default=list, blank=True)
    medications = models.JSONField(default=list, blank=True)
    allergies = models.JSONField(default=list, blank=True)
    
    # Vital Signs (if applicable)
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)
    temperature = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    respiratory_rate = models.IntegerField(null=True, blank=True)
    oxygen_saturation = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # in cm
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # in kg
    bmi = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    # Status and Priority
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_confidential = models.BooleanField(default=False)
    requires_follow_up = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    
    # Audit Trail
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, related_name='created_medical_records')
    last_modified_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, related_name='modified_medical_records')
    
    class Meta:
        ordering = ['-date_recorded', '-created_at']
        indexes = [
            models.Index(fields=['patient', 'record_type']),
            models.Index(fields=['date_recorded']),
            models.Index(fields=['priority', 'requires_follow_up']),
        ]
        verbose_name = 'Medical Record'
        verbose_name_plural = 'Medical Records'
    
    def __str__(self):
        return f"{self.record_type}: {self.title} - {self.patient}"
    
    def clean(self):
        if self.date_effective and self.date_effective > timezone.now().date():
            raise ValidationError({'date_effective': 'Effective date cannot be in the future'})
    
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            if self.blood_pressure_systolic <= self.blood_pressure_diastolic:
                raise ValidationError({'blood_pressure': 'Systolic must be greater than diastolic'})

    def save(self, *args, **kwargs):
        self.full_clean()  # Calls clean() method
        super().save(*args, **kwargs)
        # Calculate BMI if height and weight are provided
        if self.height and self.weight:
            height_in_meters = self.height / 100
            self.bmi = round(self.weight / (height_in_meters ** 2), 1)
        
        # Set file name and size if file is uploaded
        if self.file and not self.file_name:
            self.file_name = self.file.name
            self.file_size = self.file.size
        
        super().save(*args, **kwargs)
    
    @property
    def blood_pressure(self):
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None

class Allergy(models.Model):
    SEVERITY_CHOICES = (
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('life_threatening', 'Life Threatening'),
    )
    
    REACTION_CHOICES = (
        ('rash', 'Rash'),
        ('hives', 'Hives'),
        ('swelling', 'Swelling'),
        ('difficulty_breathing', 'Difficulty Breathing'),
        ('anaphylaxis', 'Anaphylaxis'),
        ('other', 'Other'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_allergies')  # Fixed: changed related_name
    allergen = models.CharField(max_length=200)
    allergen_type = models.CharField(max_length=50)  # food, drug, environmental, etc.
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    reaction = models.CharField(max_length=50, choices=REACTION_CHOICES)
    symptoms = models.TextField()
    onset_date = models.DateField(null=True, blank=True)
    diagnosed_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Allergies'
        ordering = ['-severity', 'allergen']
    
    def __str__(self):
        return f"{self.allergen} Allergy - {self.patient}"

class Diagnosis(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('chronic', 'Chronic'),
        ('ruled_out', 'Ruled Out'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='diagnoses')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='diagnoses')
    diagnosis_code = models.CharField(max_length=20)  # ICD-10 code
    description = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    date_diagnosed = models.DateField()
    date_resolved = models.DateField(null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Diagnoses'
        ordering = ['-date_diagnosed', '-is_primary']
    
    def __str__(self):
        return f"{self.diagnosis_code}: {self.description} - {self.patient}"

class MedicationHistory(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('discontinued', 'Discontinued'),
        ('on_hold', 'On Hold'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medication_history')
    prescribed_by = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='prescribed_medications')
    medication_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    route = models.CharField(max_length=50)  # oral, topical, injection, etc.
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    reason = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    effectiveness = models.CharField(max_length=20, blank=True)  # effective, ineffective, etc.
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Medication History'
        ordering = ['-start_date', 'status']
    
    def __str__(self):
        return f"{self.medication_name} - {self.patient}"

class SurgicalHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='surgical_history')
    procedure_name = models.CharField(max_length=200)
    procedure_date = models.DateField()
    surgeon = models.CharField(max_length=200)
    hospital = models.CharField(max_length=200, blank=True)
    anesthesia_type = models.CharField(max_length=100, blank=True)
    complications = models.TextField(blank=True)
    outcome = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Surgical History'
        ordering = ['-procedure_date']
    
    def __str__(self):
        return f"{self.procedure_name} - {self.patient}"

class FamilyHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='family_history')
    relation = models.CharField(max_length=100)  # mother, father, sibling, etc.
    condition = models.CharField(max_length=200)
    age_at_diagnosis = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Family History'
        ordering = ['relation']
    
    def __str__(self):
        return f"{self.relation}: {self.condition} - {self.patient}"

class ImmunizationRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='immunizations')
    vaccine_name = models.CharField(max_length=200)
    manufacturer = models.CharField(max_length=100, blank=True)
    lot_number = models.CharField(max_length=100, blank=True)
    administration_date = models.DateField()
    next_due_date = models.DateField(null=True, blank=True)
    administered_by = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-administration_date']
    
    def __str__(self):
        return f"{self.vaccine_name} - {self.patient}"

class VitalSignsRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vital_signs')
    recorded_by = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='recorded_vitals')
    recorded_date = models.DateTimeField()
    
    # Vital Signs
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)
    temperature = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    respiratory_rate = models.IntegerField(null=True, blank=True)
    oxygen_saturation = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bmi = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    # Additional Measurements
    pain_level = models.IntegerField(null=True, blank=True)  # 0-10 scale
    blood_glucose = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-recorded_date']
        verbose_name_plural = 'Vital Signs Records'
    
    def __str__(self):
        return f"Vital Signs - {self.patient} ({self.recorded_date})"
    
    def save(self, *args, **kwargs):
        # Calculate BMI if height and weight are provided
        if self.height and self.weight:
            height_in_meters = self.height / 100
            self.bmi = round(self.weight / (height_in_meters ** 2), 1)
        super().save(*args, **kwargs)
    
    @property
    def blood_pressure(self):
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None