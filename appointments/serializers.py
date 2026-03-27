from rest_framework import serializers
from django.utils import timezone
from .models import Appointment, AppointmentSlot, AppointmentReminder
from patients.serializers import PatientSerializer
from doctors.serializers import DoctorSerializer
from users.serializers import UserSerializer

class AppointmentSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    is_past_due = serializers.BooleanField(read_only=True)
    duration_minutes = serializers.FloatField(read_only=True)
    
    # Write-only fields
    patient_id = serializers.IntegerField(write_only=True)
    doctor_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'appointment_number', 'patient', 'patient_id', 'doctor', 'doctor_id',
            'appointment_date', 'duration', 'actual_start_time', 'actual_end_time',
            'appointment_type', 'reason', 'symptoms', 'priority', 'status',
            'created_by_name', 'notes', 'cancellation_reason',
            'is_past_due', 'duration_minutes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'appointment_number', 'created_at', 'updated_at', 
            'actual_start_time', 'actual_end_time'
        ]
    
    def validate_appointment_date(self, value):
        """Validate appointment date is not in the past"""
        if value < timezone.now():
            raise serializers.ValidationError("Appointment date cannot be in the past.")
        return value
    
    def validate(self, data):
        """Validate appointment constraints"""
        appointment_date = data.get('appointment_date')
        doctor_id = data.get('doctor_id')
        duration = data.get('duration', 30)
        
        if appointment_date and doctor_id:
            # Check if doctor has overlapping appointments
            from django.utils import timezone
            from datetime import timedelta
            
            end_time = appointment_date + timedelta(minutes=duration)
            
            overlapping_appointments = Appointment.objects.filter(
                doctor_id=doctor_id,
                appointment_date__lt=end_time,
                actual_start_time__gt=appointment_date,
                status__in=['scheduled', 'confirmed', 'checked_in', 'in_progress']
            ).exclude(id=self.instance.id if self.instance else None)
            
            if self.instance:
                overlapping_appointments = overlapping_appointments.exclude(id=self.instance.id)
            
            if overlapping_appointments.exists():
                raise serializers.ValidationError(
                    "Doctor has overlapping appointments during this time."
                )
        
        return data

class AppointmentCreateSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(write_only=True)
    doctor_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'patient_id', 'doctor_id', 'appointment_date', 'duration',
            'appointment_type', 'reason', 'symptoms', 'priority', 'notes'
        ]
    
    def validate(self, data):
        """Validate appointment constraints"""
        appointment_date = data.get('appointment_date')
        doctor_id = data.get('doctor_id')
        patient_id = data.get('patient_id')
        duration = data.get('duration', 30)
        
        # Validate doctor exists
        from doctors.models import Doctor
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            raise serializers.ValidationError("Doctor not found.")
        
        # Validate patient exists
        from patients.models import Patient
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            raise serializers.ValidationError("Patient not found.")
        
        # Validate appointment date is not in the past
        if appointment_date < timezone.now():
            raise serializers.ValidationError("Appointment date cannot be in the past.")
        
        # Check for overlapping appointments
        if appointment_date and doctor_id:
            from datetime import timedelta
            
            end_time = appointment_date + timedelta(minutes=duration)
            
            overlapping_appointments = Appointment.objects.filter(
                doctor_id=doctor_id,
                appointment_date__lt=end_time,
                appointment_date__gte=appointment_date - timedelta(minutes=duration),
                status__in=['scheduled', 'confirmed', 'checked_in', 'in_progress']
            )
            
            if overlapping_appointments.exists():
                raise serializers.ValidationError(
                    "Doctor has overlapping appointments during this time."
                )
        
        return data
    
    def create(self, validated_data):
        """Create appointment with proper foreign key relationships"""
        patient_id = validated_data.pop('patient_id')
        doctor_id = validated_data.pop('doctor_id')
        
        # Get the actual model instances
        from doctors.models import Doctor
        from patients.models import Patient
        
        doctor = Doctor.objects.get(id=doctor_id)
        patient = Patient.objects.get(id=patient_id)
        
        # Create appointment with proper foreign key references
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            **validated_data
        )
        
        return appointment

class AppointmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'status', 'appointment_date', 'duration', 'notes', 
            'cancellation_reason', 'actual_start_time', 'actual_end_time'
        ]
    
    def validate(self, data):
        status = data.get('status')
        cancellation_reason = data.get('cancellation_reason')
        
        if status == 'cancelled' and not cancellation_reason:
            raise serializers.ValidationError(
                "Cancellation reason is required when cancelling an appointment."
            )
        
        return data

class AppointmentSlotSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)
    doctor_id = serializers.IntegerField(write_only=True)
    is_fully_booked = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = AppointmentSlot
        fields = '__all__'

class AppointmentReminderSerializer(serializers.ModelSerializer):
    appointment = AppointmentSerializer(read_only=True)
    appointment_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = AppointmentReminder
        fields = '__all__'

class AvailableSlotsSerializer(serializers.Serializer):
    doctor_id = serializers.IntegerField()
    date = serializers.DateField()
    available_slots = serializers.ListField(child=serializers.DictField())

class AppointmentStatsSerializer(serializers.Serializer):
    total_appointments = serializers.IntegerField()
    completed_appointments = serializers.IntegerField()
    cancelled_appointments = serializers.IntegerField()
    no_show_count = serializers.IntegerField()
    average_duration = serializers.FloatField()