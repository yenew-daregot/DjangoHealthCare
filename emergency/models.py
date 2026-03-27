from django.db import models
from django.utils import timezone
from patients.models import Patient
from doctors.models import Doctor
from users.models import CustomUser

class EmergencyContact(models.Model):
    RELATIONSHIP_CHOICES = (
        ('parent', 'Parent'),
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('sibling', 'Sibling'),
        ('friend', 'Friend'),
        ('guardian', 'Legal Guardian'),
        ('other', 'Other'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    phone_number = models.CharField(max_length=15)
    alternate_phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False)
    can_make_medical_decisions = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_primary', 'name']
        verbose_name = 'Emergency Contact'
        verbose_name_plural = 'Emergency Contacts'
    
    def __str__(self):
        return f"{self.name} ({self.relationship}) - {self.patient}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary contact per patient
        if self.is_primary:
            EmergencyContact.objects.filter(
                patient=self.patient, 
                is_primary=True
            ).update(is_primary=False)
        super().save(*args, **kwargs)

class EmergencyRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('acknowledged', 'Acknowledged'),
        ('dispatched', 'Dispatched'),
        ('en_route', 'En Route'),
        ('arrived', 'Arrived on Scene'),
        ('transporting', 'Transporting to Hospital'),
        ('arrived_hospital', 'Arrived at Hospital'),
        ('handed_over', 'Handed Over to Medical Team'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    # Basic Information
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='emergency_requests')
    request_id = models.CharField(max_length=20, unique=True)
    
    # Location Information
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_notes = models.TextField(blank=True)
    
    # Emergency Details
    description = models.TextField()
    symptoms = models.JSONField(default=list, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    emergency_type = models.CharField(max_length=50)  # cardiac, trauma, respiratory, etc.
    
    # Vital Signs (if available)
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)
    respiratory_rate = models.IntegerField(null=True, blank=True)
    oxygen_saturation = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    temperature = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    gcs_score = models.IntegerField(null=True, blank=True)  # Glasgow Coma Scale
    pain_level = models.IntegerField(null=True, blank=True)  # 0-10 scale
    
    # Status and Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_conscious = models.BooleanField(null=True, blank=True)
    is_breathing = models.BooleanField(null=True, blank=True)
    has_allergies = models.BooleanField(null=True, blank=True)
    has_medications = models.BooleanField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    transported_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Response Team
    assigned_doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name='emergency_assignments')
    first_responder = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='first_responder_emergencies')
    
    # Ambulance Assignment
    assigned_ambulance = models.ForeignKey('Ambulance', on_delete=models.SET_NULL, null=True, blank=True, related_name='emergency_assignments')
    
    # Patient Information for Quick Access
    patient_age = models.IntegerField(null=True, blank=True)
    patient_blood_type = models.CharField(max_length=5, blank=True)
    patient_allergies = models.TextField(blank=True)
    patient_medical_history = models.TextField(blank=True)
    patient_current_medications = models.TextField(blank=True)
    
    # Location with Google Maps
    google_maps_url = models.URLField(blank=True)
    
    # Communication
    emergency_contacts_notified = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Additional Information
    medical_notes = models.TextField(blank=True)
    response_notes = models.TextField(blank=True)
    hospital_destination = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['created_at']),
            models.Index(fields=['patient', 'status']),
        ]
    
    def __str__(self):
        return f"Emergency: {self.request_id} - {self.patient}"
    
    def save(self, *args, **kwargs):
        if not self.request_id:
            self.request_id = self.generate_request_id()
        
        # Auto-populate patient information
        if self.patient and not self.patient_age:
            self.populate_patient_info()
        
        # Generate Google Maps URL if coordinates available
        if self.latitude and self.longitude and not self.google_maps_url:
            self.google_maps_url = f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        
        super().save(*args, **kwargs)
    
    def populate_patient_info(self):
        """Auto-populate patient information for quick access"""
        if hasattr(self.patient.user, 'date_of_birth') and self.patient.user.date_of_birth:
            from datetime import date
            today = date.today()
            self.patient_age = today.year - self.patient.user.date_of_birth.year
        
        self.patient_blood_type = getattr(self.patient, 'blood_type', '')
        self.patient_allergies = getattr(self.patient, 'allergies', '')
        self.patient_medical_history = getattr(self.patient, 'medical_history', '')
        
        # Get current medications from prescriptions
        try:
            from prescriptions.models import Prescription
            active_prescriptions = Prescription.objects.filter(
                patient=self.patient,
                status='active'
            ).select_related('medication')
            
            medications = [f"{p.medication.name} {p.dosage}" for p in active_prescriptions]
            self.patient_current_medications = "; ".join(medications)
        except:
            pass  # Handle case where prescriptions app is not available
    
    def generate_request_id(self):
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        return f"ERQ-{timestamp}"
    
    @property
    def response_time(self):
        if self.acknowledged_at and self.created_at:
            return (self.acknowledged_at - self.created_at).total_seconds()
        return None
    
    @property
    def transport_time(self):
        if self.arrived_at and self.dispatched_at:
            return (self.arrived_at - self.dispatched_at).total_seconds()
        return None
    
    @property
    def blood_pressure(self):
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None
    
    @property
    def estimated_arrival_time(self):
        """Calculate ETA based on ambulance location and traffic"""
        if self.assigned_ambulance and self.assigned_ambulance.current_latitude and self.assigned_ambulance.current_longitude:
            # This would integrate with Google Maps API for real ETA
            return "15-20 minutes"  # Placeholder
        return None

class EmergencyResponseTeam(models.Model):
    ROLE_CHOICES = (
        ('paramedic', 'Paramedic'),
        ('nurse', 'Emergency Nurse'),
        ('doctor', 'Emergency Doctor'),
        ('coordinator', 'Coordinator'),
        ('driver', 'Ambulance Driver'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('on_call', 'On Call'),
        ('on_duty', 'On Duty'),
        ('off_duty', 'Off Duty'),
        ('busy', 'Busy'),
    )
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='emergency_team_member')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    specialization = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    certification_level = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    is_active = models.BooleanField(default=True)
    current_location = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=15)
    can_prescribe = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['role', 'user__first_name']
        verbose_name = 'Emergency Response Team Member'
        verbose_name_plural = 'Emergency Response Team'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role}"

class EmergencyResponse(models.Model):
    emergency_request = models.OneToOneField(EmergencyRequest, on_delete=models.CASCADE, related_name='response')
    team_leader = models.ForeignKey(EmergencyResponseTeam, on_delete=models.SET_NULL, null=True, related_name='led_responses')
    team_members = models.ManyToManyField(EmergencyResponseTeam, related_name='assigned_responses', blank=True)
    
    # Response Details
    ambulance_number = models.CharField(max_length=20, blank=True)
    equipment_used = models.JSONField(default=list, blank=True)
    medications_administered = models.JSONField(default=list, blank=True)
    procedures_performed = models.JSONField(default=list, blank=True)
    
    # Vital Signs During Response
    initial_vitals = models.JSONField(default=dict, blank=True)
    ongoing_vitals = models.JSONField(default=list, blank=True)
    final_vitals = models.JSONField(default=dict, blank=True)
    
    # Response Timeline
    dispatch_time = models.DateTimeField(null=True, blank=True)
    en_route_time = models.DateTimeField(null=True, blank=True)
    scene_arrival_time = models.DateTimeField(null=True, blank=True)
    patient_contact_time = models.DateTimeField(null=True, blank=True)
    departure_time = models.DateTimeField(null=True, blank=True)
    hospital_arrival_time = models.DateTimeField(null=True, blank=True)
    
    # Documentation
    assessment_notes = models.TextField(blank=True)
    treatment_notes = models.TextField(blank=True)
    handover_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Emergency Responses'
    
    def __str__(self):
        return f"Response for {self.emergency_request}"

class EmergencyAlert(models.Model):
    ALERT_TYPE_CHOICES = (
        ('sos', 'SOS Alert'),
        ('fall_detection', 'Fall Detection'),
        ('heart_attack', 'Possible Heart Attack'),
        ('stroke', 'Possible Stroke'),
        ('allergic_reaction', 'Severe Allergic Reaction'),
        ('overdose', 'Possible Overdose'),
        ('seizure', 'Seizure'),
        ('diabetic_emergency', 'Diabetic Emergency'),
        ('auto_generated', 'Auto-generated'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='emergency_alerts')
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    message = models.TextField(blank=True)
    sensor_data = models.JSONField(default=dict, blank=True)  # For wearable device data
    is_auto_generated = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Alert: {self.alert_type} - {self.patient}"

class EmergencyProtocol(models.Model):
    PROTOCOL_TYPE_CHOICES = (
        ('cardiac_arrest', 'Cardiac Arrest'),
        ('stroke', 'Stroke'),
        ('trauma', 'Trauma'),
        ('respiratory_distress', 'Respiratory Distress'),
        ('allergic_reaction', 'Allergic Reaction'),
        ('seizure', 'Seizure'),
        ('overdose', 'Overdose'),
        ('diabetic_emergency', 'Diabetic Emergency'),
        ('general', 'General Emergency'),
    )
    
    name = models.CharField(max_length=100)
    protocol_type = models.CharField(max_length=30, choices=PROTOCOL_TYPE_CHOICES)
    description = models.TextField()
    steps = models.JSONField(default=list)  # List of step objects
    medications = models.JSONField(default=list, blank=True)
    equipment = models.JSONField(default=list, blank=True)
    vital_thresholds = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    version = models.CharField(max_length=10, default='1.0')
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['protocol_type', 'name']
        unique_together = ['protocol_type', 'version']
    
    def __str__(self):
        return f"{self.name} v{self.version}"

class EmergencyStatistics(models.Model):
    date = models.DateField(unique=True)
    total_emergencies = models.IntegerField(default=0)
    responded_emergencies = models.IntegerField(default=0)
    average_response_time = models.FloatField(default=0)  # in seconds
    most_common_emergency = models.CharField(max_length=50, blank=True)
    critical_cases = models.IntegerField(default=0)
    successful_outcomes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Emergency Statistics'
    
    def __str__(self):
        return f"Stats for {self.date}"

# Enhanced Models for Ambulance Tracking and Google Maps Integration

class Ambulance(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('dispatched', 'Dispatched'),
        ('en_route', 'En Route'),
        ('on_scene', 'On Scene'),
        ('transporting', 'Transporting'),
        ('at_hospital', 'At Hospital'),
        ('out_of_service', 'Out of Service'),
        ('maintenance', 'Maintenance'),
    )
    
    AMBULANCE_TYPES = (
        ('basic', 'Basic Life Support (BLS)'),
        ('advanced', 'Advanced Life Support (ALS)'),
        ('critical_care', 'Critical Care Transport'),
        ('air_ambulance', 'Air Ambulance'),
        ('bariatric', 'Bariatric Ambulance'),
    )
    
    # Basic Information
    ambulance_id = models.CharField(max_length=20, unique=True)
    license_plate = models.CharField(max_length=15, unique=True)
    ambulance_type = models.CharField(max_length=20, choices=AMBULANCE_TYPES, default='basic')
    
    # Current Status and Location
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_location = models.CharField(max_length=255, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    
    # Equipment and Capabilities
    equipment_list = models.JSONField(default=list, blank=True)
    max_capacity = models.IntegerField(default=2)  # Number of patients
    has_ventilator = models.BooleanField(default=False)
    has_defibrillator = models.BooleanField(default=True)
    has_cardiac_monitor = models.BooleanField(default=True)
    
    # Crew Information
    driver = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='driven_ambulances')
    paramedic = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='paramedic_ambulances')
    additional_crew = models.ManyToManyField(CustomUser, blank=True, related_name='crew_ambulances')
    
    # Vehicle Information
    make_model = models.CharField(max_length=100)
    year = models.IntegerField()
    vin_number = models.CharField(max_length=17, unique=True)
    fuel_level = models.DecimalField(max_digits=3, decimal_places=1, default=100.0)  # Percentage
    mileage = models.IntegerField(default=0)
    
    # Maintenance and Service
    last_service_date = models.DateField(null=True, blank=True)
    next_service_due = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Base Station
    base_station = models.ForeignKey('Hospital', on_delete=models.SET_NULL, null=True, blank=True, related_name='ambulances')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['ambulance_id']
    
    def __str__(self):
        return f"Ambulance {self.ambulance_id} - {self.status}"
    
    def update_location(self, latitude, longitude, location_name=None):
        """Update ambulance location with GPS coordinates"""
        self.current_latitude = latitude
        self.current_longitude = longitude
        if location_name:
            self.current_location = location_name
        self.last_location_update = timezone.now()
        self.save()
    
    def calculate_distance_to(self, latitude, longitude):
        """Calculate distance to given coordinates using Haversine formula"""
        if not self.current_latitude or not self.current_longitude:
            return None
        
        import math
        
        # Convert to radians
        lat1, lon1 = math.radians(float(self.current_latitude)), math.radians(float(self.current_longitude))
        lat2, lon2 = math.radians(float(latitude)), math.radians(float(longitude))
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Earth's radius in kilometers
        
        return c * r
    
    @property
    def is_available(self):
        return self.status == 'available' and self.is_active
    
    @classmethod
    def find_nearest_available(cls, latitude, longitude, ambulance_type=None):
        """Find the nearest available ambulance to given coordinates"""
        available_ambulances = cls.objects.filter(
            status='available',
            is_active=True,
            current_latitude__isnull=False,
            current_longitude__isnull=False
        )
        
        if ambulance_type:
            available_ambulances = available_ambulances.filter(ambulance_type=ambulance_type)
        
        if not available_ambulances.exists():
            return None
        
        # Calculate distances and find nearest
        nearest_ambulance = None
        min_distance = float('inf')
        
        for ambulance in available_ambulances:
            distance = ambulance.calculate_distance_to(latitude, longitude)
            if distance and distance < min_distance:
                min_distance = distance
                nearest_ambulance = ambulance
        
        return nearest_ambulance

class Hospital(models.Model):
    HOSPITAL_TYPES = (
        ('general', 'General Hospital'),
        ('specialty', 'Specialty Hospital'),
        ('trauma_center', 'Trauma Center'),
        ('children', 'Children\'s Hospital'),
        ('psychiatric', 'Psychiatric Hospital'),
        ('rehabilitation', 'Rehabilitation Hospital'),
    )
    
    # Basic Information
    name = models.CharField(max_length=200)
    hospital_type = models.CharField(max_length=20, choices=HOSPITAL_TYPES, default='general')
    
    # Location
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Contact Information
    phone_number = models.CharField(max_length=15)
    emergency_phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # Capabilities
    has_emergency_department = models.BooleanField(default=True)
    has_trauma_center = models.BooleanField(default=False)
    trauma_level = models.CharField(max_length=10, blank=True)  # Level I, II, III, IV
    has_helicopter_pad = models.BooleanField(default=False)
    bed_capacity = models.IntegerField(default=0)
    icu_beds = models.IntegerField(default=0)
    
    # Current Status
    current_wait_time = models.IntegerField(default=0)  # in minutes
    accepts_ambulances = models.BooleanField(default=True)
    is_on_diversion = models.BooleanField(default=False)  # Emergency department diversion
    
    # Operating Hours
    operates_24_7 = models.BooleanField(default=True)
    emergency_hours = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def calculate_distance_to(self, latitude, longitude):
        """Calculate distance to given coordinates"""
        if not self.latitude or not self.longitude:
            return None
        
        import math
        
        # Convert to radians
        lat1, lon1 = math.radians(float(self.latitude)), math.radians(float(self.longitude))
        lat2, lon2 = math.radians(float(latitude)), math.radians(float(longitude))
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Earth's radius in kilometers
        
        return c * r
    
    @classmethod
    def find_nearest_hospitals(cls, latitude, longitude, limit=5):
        """Find nearest hospitals to given coordinates"""
        hospitals = cls.objects.filter(
            is_active=True,
            has_emergency_department=True,
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        hospital_distances = []
        for hospital in hospitals:
            distance = hospital.calculate_distance_to(latitude, longitude)
            if distance:
                hospital_distances.append((hospital, distance))
        
        # Sort by distance and return top results
        hospital_distances.sort(key=lambda x: x[1])
        return [hospital for hospital, distance in hospital_distances[:limit]]

class EmergencyNotification(models.Model):
    NOTIFICATION_TYPES = (
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
        ('call', 'Phone Call'),
        ('in_app', 'In-App Notification'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    )
    
    emergency_request = models.ForeignKey(EmergencyRequest, on_delete=models.CASCADE, related_name='emergency_notifications')
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='emergency_notifications')
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Delivery tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    failed_reason = models.TextField(blank=True)
    
    # Retry mechanism
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} to {self.recipient} for {self.emergency_request}"