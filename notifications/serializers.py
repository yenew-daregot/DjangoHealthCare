from rest_framework import serializers
from django.utils import timezone
from .models import CustomUser
from .models import (
    Notification, NotificationTemplate, NotificationPreference,
    NotificationLog, BulkNotification, ScheduledReminder, NotificationAnalytics
)
from users.serializers import UserSerializer
from appointments.serializers import AppointmentSerializer
from prescriptions.serializers import PrescriptionSerializer
from labs.serializers import LabRequestSerializer
from emergency.serializers import EmergencyRequestSerializer
from billing.serializers import InvoiceSerializer

class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'notification_type', 'priority', 'title', 
            'message', 'short_message', 'is_read', 'is_sent', 
            'action_url', 'action_text', 'created_at', 'read_at'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'read_at', 'is_sent'
        ]

class NotificationDetailSerializer(NotificationSerializer):
    related_appointment = AppointmentSerializer(read_only=True)
    related_prescription = PrescriptionSerializer(read_only=True)
    related_lab_result = LabRequestSerializer(read_only=True)
    related_emergency = EmergencyRequestSerializer(read_only=True)
    related_invoice = InvoiceSerializer(read_only=True)
    
    class Meta(NotificationSerializer.Meta):
        fields = NotificationSerializer.Meta.fields + [
            'related_appointment', 'related_prescription', 'related_lab_result',
            'related_emergency', 'related_invoice', 'channels', 'deep_link',
            'scheduled_for', 'expires_at', 'metadata', 'updated_at'
        ]
        read_only_fields = NotificationSerializer.Meta.read_only_fields + [
            'updated_at'
        ]

class CreateNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'user', 'notification_type', 'title', 'message', 'short_message',
            'priority', 'channels', 'action_url', 'action_text', 'deep_link',
            'related_appointment', 'related_prescription', 'related_lab_result',
            'related_emergency', 'related_invoice', 'scheduled_for', 'expires_at',
            'metadata', 'template_name'
        ]
    
    def validate_channels(self, value):
        valid_channels = ['email', 'sms', 'push', 'in_app']
        for channel in value:
            if channel not in valid_channels:
                raise serializers.ValidationError(f"Invalid channel: {channel}")
        return value
    
    def validate_scheduled_for(self, value):
        if value and value < timezone.now():
            raise serializers.ValidationError("Scheduled time cannot be in the past")
        return value

class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

class UpdatePreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'email_enabled', 'sms_enabled', 'push_enabled', 'in_app_enabled',
            'appointment_notifications', 'prescription_notifications',
            'lab_result_notifications', 'billing_notifications',
            'emergency_notifications', 'chat_notifications',
            'system_notifications', 'reminder_notifications',
            'health_alert_notifications', 'announcement_notifications',
            'quiet_hours_start', 'quiet_hours_end', 'timezone',
            'digest_frequency'
        ]

class NotificationLogSerializer(serializers.ModelSerializer):
    notification = NotificationSerializer(read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = '__all__'
        read_only_fields = ['created_at']

class BulkNotificationSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    template = NotificationTemplateSerializer(read_only=True)
    target_users = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = BulkNotification
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'sent_at', 'total_recipients', 'successful_deliveries', 'failed_deliveries']

class CreateBulkNotificationSerializer(serializers.ModelSerializer):
    target_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    
    class Meta:
        model = BulkNotification
        fields = [
            'name', 'target_audience', 'template', 'custom_message',
            'scheduled_for', 'target_user_ids'
        ]
    
    def validate_target_audience(self, value):
        if value == 'custom_list' and not self.initial_data.get('target_user_ids'):
            raise serializers.ValidationError("target_user_ids is required for custom_list audience")
        return value
    
    def create(self, validated_data):
        target_user_ids = validated_data.pop('target_user_ids', [])
        bulk_notification = BulkNotification.objects.create(**validated_data)
        
        if target_user_ids:
            users = CustomUser.objects.filter(id__in=target_user_ids)
            bulk_notification.target_users.set(users)
        
        return bulk_notification

class ScheduledReminderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    related_appointment = AppointmentSerializer(read_only=True)
    related_prescription = PrescriptionSerializer(read_only=True)
    
    class Meta:
        model = ScheduledReminder
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at', 'last_sent', 'sent_count']

class CreateReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledReminder
        fields = [
            'reminder_type', 'title', 'message', 'scheduled_time',
            'repeat_frequency', 'repeat_until', 'related_appointment',
            'related_prescription'
        ]
    
    def validate_scheduled_time(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Scheduled time cannot be in the past")
        return value
    
    def validate(self, data):
        if data.get('repeat_frequency') != 'once' and not data.get('repeat_until'):
            raise serializers.ValidationError("repeat_until is required for recurring reminders")
        
        if data.get('repeat_until') and data.get('scheduled_time'):
            if data['repeat_until'] <= data['scheduled_time']:
                raise serializers.ValidationError("repeat_until must be after scheduled_time")
        
        return data

class NotificationAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationAnalytics
        fields = '__all__'
        read_only_fields = ['created_at']

class TestNotificationSerializer(serializers.Serializer):
    notification_type = serializers.ChoiceField(
        choices=Notification.NOTIFICATION_TYPES,
        default='system'
    )
    channels = serializers.ListField(
        child=serializers.ChoiceField(choices=Notification.NOTIFICATION_CHANNELS),
        default=['in_app']
    )

class MobileDeviceSerializer(serializers.Serializer):
    device_token = serializers.CharField(max_length=255)
    platform = serializers.ChoiceField(choices=[('ios', 'iOS'), ('android', 'Android')])

# Specialized notification serializers for different types
class AppointmentNotificationSerializer(serializers.Serializer):
    appointment_id = serializers.IntegerField()
    notification_type = serializers.ChoiceField(choices=[
        ('reminder', 'Reminder'),
        ('confirmation', 'Confirmation'),
        ('cancellation', 'Cancellation'),
        ('reschedule', 'Reschedule')
    ])

class PrescriptionNotificationSerializer(serializers.Serializer):
    prescription_id = serializers.IntegerField()
    notification_type = serializers.ChoiceField(choices=[
        ('ready', 'Ready for Pickup'),
        ('refill', 'Refill Reminder'),
        ('expiry', 'Expiry Warning')
    ])

class LabResultNotificationSerializer(serializers.Serializer):
    lab_request_id = serializers.IntegerField()
    notification_type = serializers.ChoiceField(choices=[
        ('ready', 'Results Ready'),
        ('abnormal', 'Abnormal Results'),
        ('critical', 'Critical Results')
    ])

class BillingNotificationSerializer(serializers.Serializer):
    invoice_id = serializers.IntegerField()
    notification_type = serializers.ChoiceField(choices=[
        ('due', 'Payment Due'),
        ('overdue', 'Payment Overdue'),
        ('paid', 'Payment Confirmed'),
        ('refund', 'Refund Processed')
    ])