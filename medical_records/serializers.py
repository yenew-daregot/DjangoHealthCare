from rest_framework import serializers
from django.utils import timezone
from .models import (
    MedicalRecord, Allergy, Diagnosis, MedicationHistory,
    SurgicalHistory, FamilyHistory, ImmunizationRecord, VitalSignsRecord
)
from patients.serializers import PatientSerializer
from doctors.serializers import DoctorSerializer
from users.serializers import UserSerializer
from patients.models import Patient 
from doctors.models import Doctor
class AllergySerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    diagnosed_by = DoctorSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    diagnosed_by_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Allergy
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class DiagnosisSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    doctor_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Diagnosis
        fields = '__all__'
        read_only_fields = ['created_at']

class MedicationHistorySerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    prescribed_by = DoctorSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    prescribed_by_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = MedicationHistory
        fields = '__all__'
        read_only_fields = ['created_at']

class SurgicalHistorySerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = SurgicalHistory
        fields = '__all__'
        read_only_fields = ['created_at']

class FamilyHistorySerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = FamilyHistory
        fields = '__all__'
        read_only_fields = ['created_at']

class ImmunizationRecordSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ImmunizationRecord
        fields = '__all__'
        read_only_fields = ['created_at']

class VitalSignsRecordSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    recorded_by = DoctorSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    recorded_by_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = VitalSignsRecord
        fields = '__all__'
        read_only_fields = ['created_at', 'bmi']

class MedicalRecordSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    last_modified_by = UserSerializer(read_only=True)
    
    # Write-only fields
    patient_id = serializers.IntegerField(write_only=True)
    doctor_id = serializers.IntegerField(write_only=True)
    appointment_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    lab_request_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    prescription_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    created_by_id = serializers.IntegerField(write_only=True, required=False)
    last_modified_by_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = MedicalRecord
        fields = '__all__'
        read_only_fields = [
            'created_at', 'updated_at', 'file_size', 'bmi',
            'created_by', 'last_modified_by'
        ]
    def validate(self, data):
        # Ensure follow_up_date is provided if requires_follow_up is True
        if data.get('requires_follow_up') and not data.get('follow_up_date'):
            raise serializers.ValidationError({
                'follow_up_date': 'Follow-up date is required when follow-up is needed'
            })
        
        # Validate date_effective is not in future
        if data.get('date_effective') and data['date_effective'] > timezone.now().date():
            raise serializers.ValidationError({
                'date_effective': 'Effective date cannot be in the future'
            })
        
        return data


class MedicalRecordDetailSerializer(MedicalRecordSerializer):
    # Extended serializer with more detailed information
    blood_pressure = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicalRecord
        fields = '__all__'
        read_only_fields = [
            'created_at', 'updated_at', 'file_size', 'bmi',
            'created_by', 'last_modified_by'
        ]
    
    def get_blood_pressure(self, obj):
        return obj.blood_pressure

class MedicalRecordFileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    record_type = serializers.CharField(max_length=20)
    patient_id = serializers.IntegerField()
    doctor_id = serializers.IntegerField()
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    
    def validate_file(self, value):
        # Validate file size (max 25MB for medical records)
        max_size = 25 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("File size must be less than 25MB.")
        
        # Validate file types
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'application/pdf',
            'application/msword', 'text/plain',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ]
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("File type not allowed.")
        
        return value

class PatientMedicalSummarySerializer(serializers.Serializer):
    patient = PatientSerializer()
    recent_records = MedicalRecordSerializer(many=True)
    active_diagnoses = DiagnosisSerializer(many=True)
    current_medications = MedicationHistorySerializer(many=True)
    active_allergies = AllergySerializer(many=True)
    recent_vitals = VitalSignsRecordSerializer(many=True)
    upcoming_immunizations = ImmunizationRecordSerializer(many=True)
    statistics = serializers.DictField()

class PatientTimelineSerializer(serializers.Serializer):
    type = serializers.CharField()
    date = serializers.DateTimeField()
    title = serializers.CharField()
    description = serializers.CharField()
    data = serializers.DictField()

class CreateMedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = [
            'patient_id', 'doctor_id', 'record_type', 'title', 'description',
            'clinical_notes', 'date_recorded', 'date_effective', 'appointment_id',
            'lab_request_id', 'prescription_id', 'diagnosis_codes', 'procedure_codes',
            'symptoms', 'medications', 'allergies', 'blood_pressure_systolic',
            'blood_pressure_diastolic', 'heart_rate', 'temperature', 'respiratory_rate',
            'oxygen_saturation', 'height', 'weight', 'priority', 'is_confidential',
            'requires_follow_up', 'follow_up_date', 'file'
        ]
    
    def validate(self, data):
        # Validate that vital signs are within reasonable ranges
        if data.get('blood_pressure_systolic'):
            if not (50 <= data['blood_pressure_systolic'] <= 250):
                raise serializers.ValidationError("Systolic blood pressure must be between 50 and 250.")
        
        if data.get('blood_pressure_diastolic'):
            if not (30 <= data['blood_pressure_diastolic'] <= 150):
                raise serializers.ValidationError("Diastolic blood pressure must be between 30 and 150.")
        
        if data.get('heart_rate'):
            if not (30 <= data['heart_rate'] <= 200):
                raise serializers.ValidationError("Heart rate must be between 30 and 200.")
        
        if data.get('temperature'):
            if not (35.0 <= data['temperature'] <= 42.0):
                raise serializers.ValidationError("Temperature must be between 35.0 and 42.0 °C.")
        
        return data

class UpdateMedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = [
            'title', 'description', 'clinical_notes', 'diagnosis_codes',
            'procedure_codes', 'symptoms', 'medications', 'allergies',
            'blood_pressure_systolic', 'blood_pressure_diastolic', 'heart_rate',
            'temperature', 'respiratory_rate', 'oxygen_saturation', 'height',
            'weight', 'priority', 'is_confidential', 'requires_follow_up',
            'follow_up_date'
        ]