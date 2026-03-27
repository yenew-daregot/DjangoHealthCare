from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from patients.models import Patient
from doctors.models import Doctor
from django.conf import settings

class VitalType(models.Model):
    """Defines types of vital signs that can be recorded"""
    VITAL_TYPES = [
        ('blood_pressure', 'Blood Pressure'),
        ('heart_rate', 'Heart Rate'),
        ('temperature', 'Temperature'),
        ('oxygen_saturation', 'Oxygen Saturation'),
        ('respiratory_rate', 'Respiratory Rate'),
        ('blood_sugar', 'Blood Sugar'),
        ('weight', 'Weight'),
        ('height', 'Height'),
        ('bmi', 'BMI'),
    ]
    
    name = models.CharField(max_length=50, choices=VITAL_TYPES, unique=True)
    display_name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)
    normal_min = models.FloatField(null=True, blank=True)
    normal_max = models.FloatField(null=True, blank=True)
    critical_min = models.FloatField(null=True, blank=True)
    critical_max = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.display_name
    
    class Meta:
        db_table = 'health_vital_types'

class VitalReading(models.Model):
    """Records vital sign readings for patients"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vital_readings')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name='health_vitals_recorded')
    vital_type = models.CharField(max_length=50, choices=VitalType.VITAL_TYPES)
    value = models.CharField(max_length=50)  # String to handle complex values like "120/80"
    unit = models.CharField(max_length=20)
    recorded_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    is_manual = models.BooleanField(default=True)  # True if manually entered, False if from device
    device_id = models.CharField(max_length=100, blank=True)  # For device integration
    is_abnormal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Auto-calculate if reading is abnormal
        self.is_abnormal = self.check_if_abnormal()
        super().save(*args, **kwargs)
        
        # Create alert if abnormal
        if self.is_abnormal:
            self.create_alert_if_needed()
    
    def check_if_abnormal(self):
        """Check if the vital reading is abnormal based on predefined ranges"""
        try:
            # Handle blood pressure specially
            if self.vital_type == 'blood_pressure':
                if '/' in self.value:
                    systolic, diastolic = map(float, self.value.split('/'))
                    return systolic > 140 or diastolic > 90 or systolic < 90 or diastolic < 60
            
            # Handle other vitals
            value = float(self.value)
            ranges = {
                'heart_rate': (60, 100),
                'temperature': (36.5, 37.5),
                'oxygen_saturation': (95, 100),
                'respiratory_rate': (12, 20),
                'blood_sugar': (70, 140),
            }
            
            if self.vital_type in ranges:
                min_val, max_val = ranges[self.vital_type]
                return value < min_val or value > max_val
                
        except (ValueError, TypeError):
            pass
        
        return False
    
    def create_alert_if_needed(self):
        """Create an alert if this is an abnormal reading"""
        if self.is_abnormal:
            # Check if there's already a recent alert for this patient and vital type
            recent_alert = HealthAlert.objects.filter(
                patient=self.patient,
                vital_reading=self,
                created_at__gte=timezone.now() - timezone.timedelta(hours=1)
            ).first()
            
            if not recent_alert:
                severity = 'high' if self.is_critical() else 'medium'
                HealthAlert.objects.create(
                    patient=self.patient,
                    vital_reading=self,
                    title=f'Abnormal {self.get_vital_type_display()}',
                    message=f'{self.get_vital_type_display()} reading of {self.value} {self.unit} is outside normal range',
                    severity=severity,
                    created_by=self.doctor.user if self.doctor else None
                )
    
    def is_critical(self):
        """Check if the reading is critically abnormal"""
        try:
            if self.vital_type == 'blood_pressure':
                if '/' in self.value:
                    systolic, diastolic = map(float, self.value.split('/'))
                    return systolic > 180 or diastolic > 110 or systolic < 70 or diastolic < 40
            
            value = float(self.value)
            critical_ranges = {
                'heart_rate': (40, 150),
                'temperature': (35.0, 40.0),
                'oxygen_saturation': (85, 100),
                'respiratory_rate': (8, 30),
                'blood_sugar': (40, 300),
            }
            
            if self.vital_type in critical_ranges:
                min_val, max_val = critical_ranges[self.vital_type]
                return value < min_val or value > max_val
                
        except (ValueError, TypeError):
            pass
        
        return False
    
    def __str__(self):
        return f"{self.patient} - {self.get_vital_type_display()}: {self.value} {self.unit}"
    
    class Meta:
        db_table = 'health_vital_readings'
        ordering = ['-recorded_at']

class HealthAlert(models.Model):
    """Health alerts for abnormal readings or conditions"""
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='health_alerts')
    vital_reading = models.ForeignKey(VitalReading, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_health_alerts')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_health_alerts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def resolve(self, user=None):
        """Mark alert as resolved"""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.save()
    
    def __str__(self):
        return f"{self.patient} - {self.title} ({self.severity})"
    
    class Meta:
        db_table = 'health_alerts'
        ordering = ['-created_at']

class PatientHealthSummary(models.Model):
    """Summary of patient's health status and trends"""
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='health_summary')
    last_checkup = models.DateTimeField(null=True, blank=True)
    total_readings = models.IntegerField(default=0)
    abnormal_readings = models.IntegerField(default=0)
    active_alerts = models.IntegerField(default=0)
    risk_level = models.CharField(max_length=20, choices=[
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ], default='low')
    notes = models.TextField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def update_summary(self):
        """Update the health summary based on recent data"""
        # Count readings from last 30 days
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_readings = VitalReading.objects.filter(
            patient=self.patient,
            recorded_at__gte=thirty_days_ago
        )
        
        self.total_readings = recent_readings.count()
        self.abnormal_readings = recent_readings.filter(is_abnormal=True).count()
        self.active_alerts = HealthAlert.objects.filter(
            patient=self.patient,
            is_resolved=False
        ).count()
        
        # Calculate risk level
        if self.active_alerts > 5 or (self.total_readings > 0 and self.abnormal_readings / self.total_readings > 0.5):
            self.risk_level = 'critical'
        elif self.active_alerts > 2 or (self.total_readings > 0 and self.abnormal_readings / self.total_readings > 0.3):
            self.risk_level = 'high'
        elif self.active_alerts > 0 or (self.total_readings > 0 and self.abnormal_readings / self.total_readings > 0.1):
            self.risk_level = 'medium'
        else:
            self.risk_level = 'low'
        
        self.save()
    
    def __str__(self):
        return f"{self.patient} - Health Summary"
    
    class Meta:
        db_table = 'health_patient_summaries'

class HealthReport(models.Model):
    """Generated health reports for patients or system-wide"""
    REPORT_TYPES = [
        ('patient_summary', 'Patient Summary'),
        ('vital_trends', 'Vital Trends'),
        ('alert_summary', 'Alert Summary'),
        ('system_overview', 'System Overview'),
    ]
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    data = models.JSONField()  # Store report data as JSON
    file_path = models.CharField(max_length=500, blank=True)  # Path to generated file
    is_shared_with_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%Y-%m-%d')}"
    
    class Meta:
        db_table = 'health_reports'
        ordering = ['-created_at']