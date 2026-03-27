from rest_framework import serializers
from .models import Medication, MedicationSchedule, MedicationDose, MedicationReminder
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class MedicationScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationSchedule
        fields = '__all__'

class MedicationDoseSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='medication.name', read_only=True)
    patient_username = serializers.CharField(source='medication.patient.username', read_only=True)
    
    class Meta:
        model = MedicationDose
        fields = '__all__'

class MedicationSerializer(serializers.ModelSerializer):
    schedules = MedicationScheduleSerializer(many=True, read_only=True)
    next_dose = serializers.SerializerMethodField()
    patient_username = serializers.CharField(source='patient.username', read_only=True)
    
    class Meta:
        model = Medication
        fields = [
            'id', 'name', 'generic_name', 'dosage', 'unit', 'form', 
            'category', 'manufacturer', 'stock_quantity', 'min_stock_level',
            'cost', 'price', 'requires_prescription', 'side_effects',
            'contraindications', 'storage', 'expiry_date', 'patient',
            'patient_username', 'created_at', 'updated_at', 'schedules',
            'next_dose'
        ]
        read_only_fields = ('patient', 'created_at', 'updated_at')
    
    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock quantity cannot be negative")
        return value
    
    def validate_min_stock_level(self, value):
        if value < 0:
            raise serializers.ValidationError("Minimum stock level cannot be negative")
        return value
    
    def validate_cost(self, value):
        if value < 0:
            raise serializers.ValidationError("Cost cannot be negative")
        return value
    
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative")
        return value
    
    def validate(self, data):
        expiry_date = data.get('expiry_date')
        if expiry_date and expiry_date < timezone.now().date():
            raise serializers.ValidationError({
                'expiry_date': 'Expiry date must be in the future'
            })
        return data
    
    def get_next_dose(self, obj):
        next_dose = obj.doses.filter(
            scheduled_time__gte=timezone.now(),
            is_taken=False,
            is_skipped=False
        ).first()
        
        if next_dose:
            return {
                'id': next_dose.id,
                'scheduled_time': next_dose.scheduled_time,
                'medication_id': next_dose.medication_id,
                'medication_name': next_dose.medication.name if next_dose.medication else None,
            }
        return None

class MedicationReminderSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='medication.name', read_only=True)
    patient_username = serializers.CharField(source='medication.patient.username', read_only=True)
    
    class Meta:
        model = MedicationReminder
        fields = '__all__'