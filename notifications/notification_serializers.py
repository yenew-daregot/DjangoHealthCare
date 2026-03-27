"""
Notification Serializers
"""

from rest_framework import serializers
from .models import Notification, NotificationPreference

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'title', 'message', 'notification_type', 'priority',
            'metadata', 'is_read', 'read_at', 'created_at', 'updated_at',
            'action_url', 'action_text', 'expires_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Customize the representation"""
        data = super().to_representation(instance)
        
        # Add user-friendly timestamp
        if instance.created_at:
            data['time_ago'] = self._get_time_ago(instance.created_at)
        
        # Add notification icon based on type
        data['icon'] = self._get_notification_icon(instance.notification_type)
        
        return data
    
    def _get_time_ago(self, timestamp):
        """Get human-readable time ago"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - timestamp
        
        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return timestamp.strftime("%b %d, %Y")
    
    def _get_notification_icon(self, notification_type):
        """Get icon for notification type"""
        icons = {
            'info': 'info',
            'success': 'check_circle',
            'warning': 'warning',
            'error': 'error',
            'urgent': 'priority_high',
            'emergency': 'emergency'
        }
        return icons.get(notification_type, 'notifications')

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for NotificationPreference model"""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user', 'sms_enabled', 'push_enabled', 'email_enabled',
            'in_app_enabled', 'appointment_notifications', 'health_alert_notifications',
            'emergency_notifications', 'prescription_notifications', 'lab_result_notifications',
            'billing_notifications', 'chat_notifications', 'system_notifications',
            'reminder_notifications', 'announcement_notifications',
            'quiet_hours_start', 'quiet_hours_end', 'timezone',
            'digest_frequency', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate notification preferences"""
        # Ensure at least one notification method is enabled
        if not any([
            data.get('sms_enabled', True),
            data.get('push_enabled', True),
            data.get('email_enabled', True),
            data.get('in_app_enabled', True)
        ]):
            raise serializers.ValidationError(
                "At least one notification method must be enabled"
            )
        
        # Validate quiet hours
        quiet_start = data.get('quiet_hours_start')
        quiet_end = data.get('quiet_hours_end')
        
        if quiet_start and quiet_end:
            if quiet_start >= quiet_end:
                raise serializers.ValidationError(
                    "Quiet hours start time must be before end time"
                )
        
        return data

class NotificationSummarySerializer(serializers.Serializer):
    """Serializer for notification summary data"""
    total_notifications = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    recent_notifications = NotificationSerializer(many=True)
    notification_types = serializers.DictField()
    
class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""
    total_sent = serializers.IntegerField()
    total_read = serializers.IntegerField()
    success_rate = serializers.FloatField()
    channel_stats = serializers.DictField()
    type_distribution = serializers.DictField()
    recent_activity = serializers.ListField()