from rest_framework import serializers
from .models import Prescription, Medication, PrescriptionRefill
from appointments.serializers import AppointmentSerializer
from patients.serializers import PatientSerializer
from doctors.serializers import DoctorSerializer

class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = [
            'id', 'name', 'generic_name', 'manufacturer', 'medication_type',
            'strength', 'description', 'side_effects', 'contraindications',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class CreateMedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = [
            'name', 'generic_name', 'manufacturer', 'medication_type',
            'strength', 'description', 'side_effects', 'contraindications'
        ]

class PrescriptionSerializer(serializers.ModelSerializer):
    appointment = AppointmentSerializer(read_only=True)
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    medication = MedicationSerializer(read_only=True)
    
    # Computed fields
    is_expired = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    frequency_display = serializers.ReadOnlyField()
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'prescription_id', 'appointment', 'patient', 'doctor', 'medication',
            'dosage', 'frequency', 'custom_frequency', 'frequency_display',
            'duration', 'duration_days', 'instructions', 'notes', 'status',
            'prescribed_date', 'start_date', 'end_date',
            'refills_allowed', 'refills_remaining', 'is_urgent', 'pharmacy_notes',
            'is_expired', 'days_remaining', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'prescription_id', 'patient', 'doctor', 'prescribed_date',
            'is_expired', 'days_remaining', 'created_at', 'updated_at'
        ]

class CreatePrescriptionSerializer(serializers.ModelSerializer):
    # Write-only fields for creation
    appointment_id = serializers.IntegerField(write_only=True)
    medication_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Prescription
        fields = [
            'appointment_id', 'medication_id', 'dosage', 'frequency', 'custom_frequency',
            'duration', 'duration_days', 'instructions', 'notes', 'start_date',
            'end_date', 'refills_allowed', 'is_urgent', 'pharmacy_notes'
        ]
    
    def validate_appointment_id(self, value):
        from appointments.models import Appointment
        try:
            appointment = Appointment.objects.get(id=value)
            # Check if appointment is completed or in progress
            if appointment.status not in ['completed', 'in_progress']:
                raise serializers.ValidationError("Can only prescribe for completed or in-progress appointments.")
            return value
        except Appointment.DoesNotExist:
            raise serializers.ValidationError("Appointment does not exist.")
    
    def validate_medication_id(self, value):
        try:
            medication = Medication.objects.get(id=value, is_active=True)
            return value
        except Medication.DoesNotExist:
            raise serializers.ValidationError("Medication does not exist or is inactive.")
    
    def validate(self, attrs):
        # Ensure required fields are present
        required_fields = ['dosage', 'frequency', 'duration']
        for field in required_fields:
            if not attrs.get(field, '').strip():
                raise serializers.ValidationError({field: f"{field.capitalize()} is required."})
        
        # Validate custom frequency
        if attrs.get('frequency') == 'custom' and not attrs.get('custom_frequency', '').strip():
            raise serializers.ValidationError({'custom_frequency': 'Custom frequency is required when frequency is set to custom.'})
        
        # Validate refills
        refills_allowed = attrs.get('refills_allowed', 0)
        if refills_allowed < 0:
            raise serializers.ValidationError({'refills_allowed': 'Refills allowed cannot be negative.'})
        
        return attrs
    
    def create(self, validated_data):
        # Extract foreign key IDs
        appointment_id = validated_data.pop('appointment_id')
        medication_id = validated_data.pop('medication_id')
        
        # Get the actual objects
        from appointments.models import Appointment
        appointment = Appointment.objects.get(id=appointment_id)
        medication = Medication.objects.get(id=medication_id)
        
        # Create prescription
        prescription = Prescription.objects.create(
            appointment=appointment,
            medication=medication,
            **validated_data
        )
        return prescription

class UpdatePrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = [
            'dosage', 'frequency', 'custom_frequency', 'duration', 'duration_days',
            'instructions', 'notes', 'status', 'start_date', 'end_date',
            'refills_allowed', 'refills_remaining', 'is_urgent', 'pharmacy_notes'
        ]
    
    def validate(self, attrs):
        # Validate custom frequency
        if attrs.get('frequency') == 'custom' and not attrs.get('custom_frequency', '').strip():
            raise serializers.ValidationError({'custom_frequency': 'Custom frequency is required when frequency is set to custom.'})
        
        return attrs

class PrescriptionRefillSerializer(serializers.ModelSerializer):
    prescription = PrescriptionSerializer(read_only=True)
    requested_by = serializers.StringRelatedField(read_only=True)
    approved_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = PrescriptionRefill
        fields = [
            'id', 'prescription', 'requested_by', 'approved_by', 'status',
            'quantity', 'notes', 'denial_reason', 'requested_date',
            'approved_date', 'dispensed_date'
        ]
        read_only_fields = [
            'requested_by', 'approved_by', 'requested_date',
            'approved_date', 'dispensed_date'
        ]

class CreatePrescriptionRefillSerializer(serializers.ModelSerializer):
    prescription_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = PrescriptionRefill
        fields = ['prescription_id', 'quantity', 'notes']
    
    def validate_prescription_id(self, value):
        try:
            prescription = Prescription.objects.get(id=value)
            if prescription.status != 'active':
                raise serializers.ValidationError("Can only request refills for active prescriptions.")
            if prescription.refills_remaining <= 0:
                raise serializers.ValidationError("No refills remaining for this prescription.")
            return value
        except Prescription.DoesNotExist:
            raise serializers.ValidationError("Prescription does not exist.")
    
    def create(self, validated_data):
        prescription_id = validated_data.pop('prescription_id')
        prescription = Prescription.objects.get(id=prescription_id)
        
        return PrescriptionRefill.objects.create(
            prescription=prescription,
            requested_by=self.context['request'].user,
            **validated_data
        )

# Summary serializers for dashboard views
class PrescriptionSummarySerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='medication.name', read_only=True)
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'prescription_id', 'medication_name', 'patient_name', 'doctor_name',
            'dosage', 'frequency_display', 'duration', 'status', 'prescribed_date',
            'days_remaining', 'is_expired', 'is_urgent'
        ]