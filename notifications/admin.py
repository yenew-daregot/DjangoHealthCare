from django.contrib import admin
from .models import (
    Notification, NotificationTemplate, NotificationPreference,
    NotificationLog, BulkNotification, ScheduledReminder, NotificationAnalytics
)

class NotificationLogInline(admin.TabularInline):
    model = NotificationLog
    extra = 0
    readonly_fields = ['created_at']
    can_delete = False

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'notification_type', 'title', 'priority', 'is_read', 
        'is_sent', 'created_at'
    ]
    list_filter = [
        'notification_type', 'priority', 'is_read', 'is_sent', 
        'created_at', 'scheduled_for'
    ]
    search_fields = [
        'user__username', 'user__email', 'title', 'message'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'read_at', 'sent_at', 'delivered_at'
    ]
    inlines = [NotificationLogInline]
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'notification_type', 'priority', 'channels')
        }),
        ('Content', {
            'fields': ('title', 'message', 'short_message', 'action_url', 'action_text', 'deep_link')
        }),
        ('Related Objects', {
            'fields': (
                'related_appointment', 'related_prescription', 
                'related_lab_result', 'related_emergency', 'related_invoice'
            ),
            'classes': ('collapse',)
        }),
        ('Scheduling', {
            'fields': ('scheduled_for', 'expires_at'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'is_sent', 'is_delivered', 'read_at', 'sent_at', 'delivered_at')
        }),
        ('Metadata', {
            'fields': ('metadata', 'template_name', 'language', 'created_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template_type', 'subject', 'priority', 'is_active'
    ]
    list_filter = ['template_type', 'priority', 'is_active']
    search_fields = ['name', 'subject', 'message']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = []

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'email_enabled', 'sms_enabled', 'push_enabled', 
        'in_app_enabled', 'digest_frequency'
    ]
    list_filter = [
        'email_enabled', 'sms_enabled', 'push_enabled', 'in_app_enabled',
        'digest_frequency'
    ]
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        'notification', 'channel', 'recipient', 'status', 'sent_at', 
        'delivered_at', 'retry_count'
    ]
    list_filter = ['channel', 'status', 'sent_at']
    search_fields = [
        'notification__title', 'recipient', 'provider_message_id'
    ]
    readonly_fields = ['created_at']

@admin.register(BulkNotification)
class BulkNotificationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'target_audience', 'template', 'scheduled_for', 
        'is_sent', 'total_recipients', 'created_by'
    ]
    list_filter = ['target_audience', 'is_sent', 'scheduled_for']
    search_fields = ['name', 'created_by__username']
    readonly_fields = ['created_at', 'sent_at']
    filter_horizontal = ['target_users']

@admin.register(ScheduledReminder)
class ScheduledReminderAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'reminder_type', 'title', 'scheduled_time', 
        'repeat_frequency', 'is_active', 'next_scheduled'
    ]
    list_filter = [
        'reminder_type', 'repeat_frequency', 'is_active', 
        'scheduled_time'
    ]
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at', 'updated_at', 'last_sent', 'sent_count']

@admin.register(NotificationAnalytics)
class NotificationAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'total_notifications', 'email_sent', 'sms_sent', 
        'push_sent', 'total_read', 'click_through_rate'
    ]
    list_filter = ['date']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'