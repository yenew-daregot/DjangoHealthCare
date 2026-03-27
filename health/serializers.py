from rest_framework import serializers
from django.contrib.auth.models import User
from .models import VitalType, VitalReading, HealthAlert, PatientHealthSummary, HealthReport
from patients.models import Patient
from doctors.models import Doctor

class VitalTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VitalType
        fields = '__all__'

class VitalReadingSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    vital_type_display = serializers.CharField(source='get_vital_type_display', read_only=True)
    is_abnormal = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = VitalReading
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'vital_type', 'vital_type_display', 'value', 'unit',
            'recorded_at', 'notes', 'is_manual', 'device_id',
            'is_abnormal', 'created_at', 'updated_at'
        ]
    
    def get_patient_name(self, obj):
        if obj.patient and obj.patient.user:
            return f"{obj.patient.user.first_name} {obj.patient.user.last_name}".strip()
        return "Unknown Patient"
    
    def get_doctor_name(self, obj):
        if obj.doctor and obj.doctor.user:
            return f"Dr. {obj.doctor.user.first_name} {obj.doctor.user.last_name}".strip()
        return "Unknown Doctor"
    
    def create(self, validated_data):
        # Set doctor from request user if not provided
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                doctor_profile = Doctor.objects.get(user=request.user)
                validated_data['doctor'] = doctor_profile
            except Doctor.DoesNotExist:
                pass
        
        return super().create(validated_data)

class HealthAlertSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    vital_reading_details = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    resolved_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = HealthAlert
        fields = [
            'id', 'patient', 'patient_name', 'vital_reading', 'vital_reading_details',
            'title', 'message', 'severity', 'is_resolved', 'resolved_at',
            'resolved_by', 'resolved_by_name', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
    
    def get_patient_name(self, obj):
        if obj.patient and obj.patient.user:
            return f"{obj.patient.user.first_name} {obj.patient.user.last_name}".strip()
        return "Unknown Patient"
    
    def get_vital_reading_details(self, obj):
        if obj.vital_reading:
            return {
                'type': obj.vital_reading.vital_type,
                'value': obj.vital_reading.value,
                'unit': obj.vital_reading.unit,
                'recorded_at': obj.vital_reading.recorded_at
            }
        return None
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return "System"
    
    def get_resolved_by_name(self, obj):
        if obj.resolved_by:
            return f"{obj.resolved_by.first_name} {obj.resolved_by.last_name}".strip()
        return None

class PatientHealthSummarySerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    patient_email = serializers.SerializerMethodField()
    recent_vitals = serializers.SerializerMethodField()
    recent_alerts = serializers.SerializerMethodField()
    
    class Meta:
        model = PatientHealthSummary
        fields = [
            'id', 'patient', 'patient_name', 'patient_email',
            'last_checkup', 'total_readings', 'abnormal_readings',
            'active_alerts', 'risk_level', 'notes', 'recent_vitals',
            'recent_alerts', 'last_updated', 'created_at'
        ]
    
    def get_patient_name(self, obj):
        if obj.patient and obj.patient.user:
            return f"{obj.patient.user.first_name} {obj.patient.user.last_name}".strip()
        return "Unknown Patient"
    
    def get_patient_email(self, obj):
        if obj.patient and obj.patient.user:
            return obj.patient.user.email
        return None
    
    def get_recent_vitals(self, obj):
        recent_vitals = VitalReading.objects.filter(patient=obj.patient).order_by('-recorded_at')[:5]
        return VitalReadingSerializer(recent_vitals, many=True).data
    
    def get_recent_alerts(self, obj):
        recent_alerts = HealthAlert.objects.filter(patient=obj.patient, is_resolved=False).order_by('-created_at')[:3]
        return HealthAlertSerializer(recent_alerts, many=True).data

class HealthReportSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    generated_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = HealthReport
        fields = [
            'id', 'title', 'report_type', 'patient', 'patient_name',
            'generated_by', 'generated_by_name', 'date_from', 'date_to',
            'data', 'file_path', 'is_shared_with_admin', 'created_at'
        ]
    
    def get_patient_name(self, obj):
        if obj.patient and obj.patient.user:
            return f"{obj.patient.user.first_name} {obj.patient.user.last_name}".strip()
        return "System Report"
    
    def get_generated_by_name(self, obj):
        if obj.generated_by:
            return f"{obj.generated_by.first_name} {obj.generated_by.last_name}".strip()
        return "System"

class HealthStatsSerializer(serializers.Serializer):
    """Serializer for health statistics"""
    total_patients = serializers.IntegerField()
    total_readings = serializers.IntegerField()
    total_alerts = serializers.IntegerField()
    active_alerts = serializers.IntegerField()
    abnormal_readings = serializers.IntegerField()
    readings_today = serializers.IntegerField()
    alerts_today = serializers.IntegerField()
    risk_distribution = serializers.DictField()
    vital_type_distribution = serializers.DictField()
    recent_readings = VitalReadingSerializer(many=True)
    recent_alerts = HealthAlertSerializer(many=True)

class PatientVitalTrendsSerializer(serializers.Serializer):
    """Serializer for patient vital trends"""
    patient_id = serializers.IntegerField()
    patient_name = serializers.CharField()
    vital_type = serializers.CharField()
    readings = serializers.ListField()
    average_value = serializers.FloatField()
    trend = serializers.CharField()  # 'improving', 'stable', 'declining'
    last_reading = VitalReadingSerializer()