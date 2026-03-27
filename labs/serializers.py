from rest_framework import serializers
from .models import LabRequest, LabTest, LabResult
from patients.serializers import PatientSerializer
from doctors.serializers import DoctorSerializer
from users.serializers import UserSerializer
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class LabTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTest
        fields = '__all__'

class LabResultSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = LabResult
        fields = '__all__'
        read_only_fields = ['created_date', 'updated_date']

class LabRequestSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    test = LabTestSerializer(read_only=True)
    laboratorist = UserSerializer(read_only=True)
    result = LabResultSerializer(read_only=True)
    
    patient_id = serializers.IntegerField(write_only=True)
    doctor_id = serializers.IntegerField(write_only=True)
    test_id = serializers.IntegerField(write_only=True)
    laboratorist_id = serializers.IntegerField(write_only=True, required=False)
    
    # Additional computed fields
    days_since_request = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = LabRequest
        fields = '__all__'
        read_only_fields = ['requested_date', 'assigned_date', 'sample_collected_date', 'completed_date']
    
    def get_days_since_request(self, obj):
        if obj.requested_date:
            return (timezone.now() - obj.requested_date).days
        return 0

class LabRequestCreateSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField()
    doctor_id = serializers.IntegerField()
    test_id = serializers.IntegerField()
    laboratorist_id = serializers.IntegerField(required=False)
    
    class Meta:
        model = LabRequest
        fields = ['patient_id', 'doctor_id', 'test_id', 'laboratorist_id', 'priority', 
                 'clinical_notes', 'request_document']

class LabRequestStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabRequest
        fields = ['status', 'lab_notes', 'assigned_date', 'sample_collected_date', 'completed_date']
        read_only_fields = ['assigned_date', 'sample_collected_date', 'completed_date']
    
    def update(self, instance, validated_data):
        status = validated_data.get('status')
        
        # Auto-set timestamps based on status
        if status == 'assigned' and not instance.assigned_date:
            validated_data['assigned_date'] = timezone.now()
        elif status == 'sample_collected' and not instance.sample_collected_date:
            validated_data['sample_collected_date'] = timezone.now()
        elif status == 'completed' and not instance.completed_date:
            validated_data['completed_date'] = timezone.now()
        
        return super().update(instance, validated_data)

class LabResultUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResult
        fields = ['result_text', 'result_document', 'result_values', 'interpretation', 'is_abnormal']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class LaboratoristSerializer(serializers.ModelSerializer):
    """Serializer for users with LABORATORIST role"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username