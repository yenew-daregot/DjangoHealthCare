from rest_framework import serializers
from .views import*
from .models import EmergencyStatistics, EmergencyContact, EmergencyRequest, EmergencyResponseTeam, EmergencyResponse, EmergencyAlert
from patients.serializers import PatientSerializer
from doctors.serializers import DoctorSerializer
from users.serializers import UserSerializer

class EmergencyContactSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = EmergencyContact
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class EmergencyRequestSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    assigned_doctor = DoctorSerializer(read_only=True)
    first_responder = UserSerializer(read_only=True)
    
    patient_id = serializers.IntegerField(write_only=True, required=False)
    assigned_doctor_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    first_responder_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = EmergencyRequest
        fields = [
            'id', 'request_id', 'patient', 'patient_id', 'assigned_doctor', 'assigned_doctor_id',
            'first_responder', 'first_responder_id', 'location', 'latitude', 'longitude',
            'location_notes', 'description', 'symptoms', 'priority', 'emergency_type',
            'blood_pressure_systolic', 'blood_pressure_diastolic', 'heart_rate',
            'respiratory_rate', 'oxygen_saturation', 'temperature', 'gcs_score',
            'pain_level', 'status', 'is_conscious', 'is_breathing', 'has_allergies',
            'has_medications', 'medical_notes', 'response_notes', 'hospital_destination',
            'created_at', 'acknowledged_at', 'dispatched_at', 'arrived_at',
            'transported_at', 'completed_at', 'response_time', 'transport_time'
        ]
        read_only_fields = [
            'request_id', 'created_at', 'acknowledged_at', 'dispatched_at',
            'arrived_at', 'transported_at', 'completed_at', 'response_time', 'transport_time'
        ]

class EmergencyRequestDetailSerializer(EmergencyRequestSerializer):
    blood_pressure = serializers.SerializerMethodField()
    
    class Meta(EmergencyRequestSerializer.Meta):
        fields = EmergencyRequestSerializer.Meta.fields + ['blood_pressure']
    
    def get_blood_pressure(self, obj):
        return obj.blood_pressure
    
    def get_response(self, obj):
        try:
            response = EmergencyResponse.objects.get(emergency_request=obj)
            return EmergencyResponseSerializer(response).data
        except EmergencyResponse.DoesNotExist:
            return None

class CreateEmergencyRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyRequest
        fields = [
            'location', 'latitude', 'longitude', 'location_notes',
            'description', 'symptoms', 'emergency_type', 'priority',
            'blood_pressure_systolic', 'blood_pressure_diastolic',
            'heart_rate', 'respiratory_rate', 'oxygen_saturation',
            'temperature', 'gcs_score', 'pain_level', 'is_conscious',
            'is_breathing', 'has_allergies', 'has_medications',
            'medical_notes'
        ]
    
    def validate(self, data):
        # Validate vital signs ranges
        if data.get('blood_pressure_systolic'):
            if not (50 <= data['blood_pressure_systolic'] <= 250):
                raise serializers.ValidationError("Systolic blood pressure must be between 50 and 250.")
        
        if data.get('blood_pressure_diastolic'):
            if not (30 <= data['blood_pressure_diastolic'] <= 150):
                raise serializers.ValidationError("Diastolic blood pressure must be between 30 and 150.")
        
        if data.get('heart_rate'):
            if not (30 <= data['heart_rate'] <= 200):
                raise serializers.ValidationError("Heart rate must be between 30 and 200.")
        
        if data.get('respiratory_rate'):
            if not (8 <= data['respiratory_rate'] <= 40):
                raise serializers.ValidationError("Respiratory rate must be between 8 and 40.")
        
        if data.get('oxygen_saturation'):
            if not (70 <= data['oxygen_saturation'] <= 100):
                raise serializers.ValidationError("Oxygen saturation must be between 70 and 100.")
        
        if data.get('temperature'):
            if not (35.0 <= data['temperature'] <= 42.0):
                raise serializers.ValidationError("Temperature must be between 35.0 and 42.0 °C.")
        
        if data.get('gcs_score'):
            if not (3 <= data['gcs_score'] <= 15):
                raise serializers.ValidationError("GCS score must be between 3 and 15.")
        
        if data.get('pain_level'):
            if not (0 <= data['pain_level'] <= 10):
                raise serializers.ValidationError("Pain level must be between 0 and 10.")
        
        return data

class UpdateEmergencyStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=EmergencyRequest.STATUS_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)

class AssignTeamSerializer(serializers.Serializer):
    team_member_id = serializers.IntegerField(required=False)
    doctor_id = serializers.IntegerField(required=False)

class EmergencyResponseTeamSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = EmergencyResponseTeam
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class EmergencyResponseSerializer(serializers.ModelSerializer):
    emergency_request = EmergencyRequestSerializer(read_only=True)
    team_leader = EmergencyResponseTeamSerializer(read_only=True)
    team_members = EmergencyResponseTeamSerializer(many=True, read_only=True)
    
    emergency_request_id = serializers.IntegerField(write_only=True)
    team_leader_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = EmergencyResponse
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class EmergencyAlertSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    verified_by = UserSerializer(read_only=True)
    
    patient_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = EmergencyAlert
        fields = '__all__'
        read_only_fields = ['created_at']

class EmergencyProtocolSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = EmergencyProtocol
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class EmergencyStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyStatistics
        fields = '__all__'
        read_only_fields = ['created_at']

class UpdateVitalsSerializer(serializers.Serializer):
    blood_pressure_systolic = serializers.IntegerField(required=False, min_value=50, max_value=250)
    blood_pressure_diastolic = serializers.IntegerField(required=False, min_value=30, max_value=150)
    heart_rate = serializers.IntegerField(required=False, min_value=30, max_value=200)
    respiratory_rate = serializers.IntegerField(required=False, min_value=8, max_value=40)
    oxygen_saturation = serializers.DecimalField(required=False, max_digits=3, decimal_places=1, min_value=70, max_value=100)
    temperature = serializers.DecimalField(required=False, max_digits=3, decimal_places=1, min_value=35.0, max_value=42.0)
    gcs_score = serializers.IntegerField(required=False, min_value=3, max_value=15)
    pain_level = serializers.IntegerField(required=False, min_value=0, max_value=10)
    is_conscious = serializers.BooleanField(required=False)
    is_breathing = serializers.BooleanField(required=False)

class SOSAlertSerializer(serializers.Serializer):
    location = serializers.CharField(max_length=255)
    latitude = serializers.DecimalField(required=False, max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(required=False, max_digits=9, decimal_places=6)
    message = serializers.CharField(required=False, allow_blank=True)

class EmergencyLocationSerializer(serializers.Serializer):
    location = serializers.CharField(max_length=255)
    latitude = serializers.DecimalField(required=False, max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(required=False, max_digits=9, decimal_places=6)
    location_notes = serializers.CharField(required=False, allow_blank=True)