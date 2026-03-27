from rest_framework import serializers
from .models import Doctor, DoctorSchedule, ScheduleException, DoctorAvailability


class DoctorScheduleSerializer(serializers.ModelSerializer):
    day_name = serializers.SerializerMethodField()
    available_slots = serializers.SerializerMethodField()
    
    class Meta:
        model = DoctorSchedule
        fields = [
            'id', 'day_of_week', 'day_name', 'start_time', 'end_time',
            'is_active', 'break_start', 'break_end', 'slot_duration',
            'max_patients_per_slot', 'notes', 'available_slots',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_day_name(self, obj):
        return dict(DoctorSchedule.DAYS_OF_WEEK)[obj.day_of_week]
    
    def get_available_slots(self, obj):
        # Only include slots if specifically requested
        request = self.context.get('request')
        if request and request.query_params.get('include_slots') == 'true':
            return obj.get_available_slots()
        return None
    
    def validate(self, data):
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("Start time must be before end time")
        
        if data.get('break_start') and data.get('break_end'):
            if data['break_start'] >= data['break_end']:
                raise serializers.ValidationError("Break start time must be before break end time")
            if not (data['start_time'] <= data['break_start'] < data['break_end'] <= data['end_time']):
                raise serializers.ValidationError("Break time must be within working hours")
        
        return data


class ScheduleExceptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleException
        fields = [
            'id', 'date', 'exception_type', 'start_time', 'end_time',
            'is_available', 'reason', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError("Start time must be before end time")
        return data


class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DoctorAvailability
        fields = [
            'is_online', 'last_seen', 'status_message',
            'auto_accept_appointments', 'emergency_available',
            'doctor_name', 'updated_at'
        ]
        read_only_fields = ['last_seen', 'updated_at', 'doctor_name']
    
    def get_doctor_name(self, obj):
        return obj.doctor.full_name


class WeeklyScheduleSerializer(serializers.Serializer):
    """Serializer for weekly schedule view"""
    monday = DoctorScheduleSerializer(many=True, read_only=True)
    tuesday = DoctorScheduleSerializer(many=True, read_only=True)
    wednesday = DoctorScheduleSerializer(many=True, read_only=True)
    thursday = DoctorScheduleSerializer(many=True, read_only=True)
    friday = DoctorScheduleSerializer(many=True, read_only=True)
    saturday = DoctorScheduleSerializer(many=True, read_only=True)
    sunday = DoctorScheduleSerializer(many=True, read_only=True)
    exceptions = ScheduleExceptionSerializer(many=True, read_only=True)
    availability = DoctorAvailabilitySerializer(read_only=True)


class ScheduleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating multiple schedule entries at once"""
    days = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=6),
        write_only=True
    )
    
    class Meta:
        model = DoctorSchedule
        fields = [
            'days', 'start_time', 'end_time', 'break_start', 'break_end',
            'slot_duration', 'max_patients_per_slot', 'notes'
        ]
    
    def create(self, validated_data):
        days = validated_data.pop('days')
        doctor = self.context['request'].user.doctor_profile
        
        schedules = []
        for day in days:
            schedule_data = validated_data.copy()
            schedule_data['day_of_week'] = day
            schedule_data['doctor'] = doctor
            
            # Check if schedule already exists for this day
            existing = DoctorSchedule.objects.filter(
                doctor=doctor,
                day_of_week=day
            ).first()
            
            if existing:
                # Update existing
                for key, value in schedule_data.items():
                    if key != 'doctor':
                        setattr(existing, key, value)
                existing.save()
                schedules.append(existing)
            else:
                # Create new
                schedule = DoctorSchedule.objects.create(**schedule_data)
                schedules.append(schedule)
        
        return schedules


class AvailableSlotsSerializer(serializers.Serializer):
    """Serializer for available time slots"""
    date = serializers.DateField()
    slots = serializers.ListField(
        child=serializers.DictField(), read_only=True
    )
    
    def to_representation(self, instance):
        # instance should be a dict with date and slots
        return {
            'date': instance['date'],
            'slots': instance['slots']
        }