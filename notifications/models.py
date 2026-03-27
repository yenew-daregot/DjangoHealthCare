from django.db import models
from django.utils import timezone
from users.models import CustomUser
from appointments.models import Appointment
from prescriptions.models import Prescription
from labs.models import LabRequest
from emergency.models import EmergencyRequest
from billing.models import Invoice


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('appointment', 'Appointment'),
        ('prescription', 'Prescription'),
        ('lab_result', 'Lab Result'),
        ('billing', 'Billing'),
        ('emergency', 'Emergency'),
        ('chat', 'Chat Message'),
        ('system', 'System'),
        ('reminder', 'Reminder'),
        ('health_alert', 'Health Alert'),
        ('announcement', 'Announcement'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    NOTIFICATION_CHANNELS = (
        ('in_app', 'In-App'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('all', 'All Channels'),
    )
    
    # Basic Information
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    channels = models.JSONField(default=list)  # List of channels to send through
    
    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()
    short_message = models.CharField(max_length=100, blank=True)  # For SMS/push notifications
    
    # Related Objects
    related_appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_lab_result = models.ForeignKey(LabRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_emergency = models.ForeignKey(EmergencyRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    
    # Action and Navigation
    action_url = models.URLField(blank=True)  # URL to navigate when notification is clicked
    action_text = models.CharField(max_length=50, blank=True)  # Text for action button
    deep_link = models.CharField(max_length=500, blank=True)  # Deep link for mobile apps
    
    # Status and Delivery
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Scheduling
    scheduled_for = models.DateTimeField(null=True, blank=True)  # For scheduled notifications
    expires_at = models.DateTimeField(null=True, blank=True)  # When notification becomes irrelevant
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)  # Additional data for processing
    template_name = models.CharField(max_length=100, blank=True)  # Template used for this notification
    language = models.CharField(max_length=10, default='en')  # Language for localization
    
    # Audit
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['scheduled_for', 'is_sent']),
            models.Index(fields=['priority', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type}: {self.title} - {self.user}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def mark_as_sent(self):
        if not self.is_sent:
            self.is_sent = True
            self.sent_at = timezone.now()
            self.save()
    
    def mark_as_delivered(self):
        if not self.is_delivered:
            self.is_delivered = True
            self.delivered_at = timezone.now()
            self.save()
    
    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def should_send(self):
        if self.scheduled_for:
            return timezone.now() >= self.scheduled_for and not self.is_sent
        return not self.is_sent

class NotificationTemplate(models.Model):
    TEMPLATE_TYPES = (
        ('appointment_reminder', 'Appointment Reminder'),
        ('appointment_confirmation', 'Appointment Confirmation'),
        ('appointment_cancellation', 'Appointment Cancellation'),
        ('prescription_ready', 'Prescription Ready'),
        ('lab_result_ready', 'Lab Result Ready'),
        ('payment_due', 'Payment Due'),
        ('payment_confirmation', 'Payment Confirmation'),
        ('emergency_alert', 'Emergency Alert'),
        ('chat_message', 'Chat Message'),
        ('system_maintenance', 'System Maintenance'),
        ('health_tip', 'Health Tip'),
        ('medication_reminder', 'Medication Reminder'),
    )
    
    name = models.CharField(max_length=100, unique=True)
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPES)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    short_message = models.CharField(max_length=100, blank=True)
    action_url_template = models.CharField(max_length=500, blank=True)
    action_text = models.CharField(max_length=50, blank=True)
    priority = models.CharField(max_length=10, choices=Notification.PRIORITY_LEVELS, default='medium')
    default_channels = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    variables = models.JSONField(default=list, blank=True)  # Available variables for template
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['template_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"

class NotificationPreference(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Channel Preferences
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)
    
    # Notification Type Preferences
    appointment_notifications = models.BooleanField(default=True)
    prescription_notifications = models.BooleanField(default=True)
    lab_result_notifications = models.BooleanField(default=True)
    billing_notifications = models.BooleanField(default=True)
    emergency_notifications = models.BooleanField(default=True)
    chat_notifications = models.BooleanField(default=True)
    system_notifications = models.BooleanField(default=True)
    reminder_notifications = models.BooleanField(default=True)
    health_alert_notifications = models.BooleanField(default=True)
    announcement_notifications = models.BooleanField(default=True)
    
    # Timing Preferences
    quiet_hours_start = models.TimeField(null=True, blank=True)  # 22:00
    quiet_hours_end = models.TimeField(null=True, blank=True)    # 08:00
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Frequency Preferences
    digest_frequency = models.CharField(
        max_length=20,
        choices=(
            ('immediate', 'Immediate'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ),
        default='immediate'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification Preferences - {self.user}"

class NotificationLog(models.Model):
    DELIVERY_STATUS = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    )
    
    CHANNEL_TYPES = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App'),
    )
    
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='delivery_logs')
    channel = models.CharField(max_length=10, choices=CHANNEL_TYPES)
    recipient = models.CharField(max_length=255)  # email, phone number, device token
    status = models.CharField(max_length=10, choices=DELIVERY_STATUS, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    provider_message_id = models.CharField(max_length=100, blank=True)  # ID from email/SMS provider
    retry_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification', 'channel']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.channel} delivery for {self.notification}"

class BulkNotification(models.Model):
    TARGET_AUDIENCE = (
        ('all_patients', 'All Patients'),
        ('all_doctors', 'All Doctors'),
        ('all_users', 'All Users'),
        ('specific_patients', 'Specific Patients'),
        ('specific_doctors', 'Specific Doctors'),
        ('custom_list', 'Custom List'),
    )
    
    name = models.CharField(max_length=200)
    target_audience = models.CharField(max_length=20, choices=TARGET_AUDIENCE)
    target_users = models.ManyToManyField(CustomUser, blank=True, related_name='bulk_notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    custom_message = models.TextField(blank=True)  # Override template message if needed
    scheduled_for = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    total_recipients = models.IntegerField(default=0)
    successful_deliveries = models.IntegerField(default=0)
    failed_deliveries = models.IntegerField(default=0)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_bulk_notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Bulk: {self.name}"

class ScheduledReminder(models.Model):
    REMINDER_TYPES = (
        ('appointment', 'Appointment Reminder'),
        ('medication', 'Medication Reminder'),
        ('follow_up', 'Follow-up Reminder'),
        ('payment', 'Payment Reminder'),
        ('health_check', 'Health Check Reminder'),
        ('vaccination', 'Vaccination Reminder'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='scheduled_reminders')
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Scheduling
    scheduled_time = models.DateTimeField()
    repeat_frequency = models.CharField(
        max_length=20,
        choices=(
            ('once', 'Once'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('custom', 'Custom'),
        ),
        default='once'
    )
    repeat_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Related Object
    related_appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, null=True, blank=True)
    related_prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, null=True, blank=True)
    
    # Metadata
    last_sent = models.DateTimeField(null=True, blank=True)
    next_scheduled = models.DateTimeField()
    sent_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['next_scheduled']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['next_scheduled', 'is_active']),
        ]
    
    def __str__(self):
        return f"Reminder: {self.title} - {self.user}"
    
    def calculate_next_scheduled(self):
        if self.repeat_frequency == 'once':
            return None
        elif self.repeat_frequency == 'daily':
            return self.next_scheduled + timezone.timedelta(days=1)
        elif self.repeat_frequency == 'weekly':
            return self.next_scheduled + timezone.timedelta(weeks=1)
        elif self.repeat_frequency == 'monthly':
            return self.next_scheduled + timezone.timedelta(days=30)
        return None

class NotificationAnalytics(models.Model):
    date = models.DateField(unique=True)
    total_notifications = models.IntegerField(default=0)
    email_sent = models.IntegerField(default=0)
    sms_sent = models.IntegerField(default=0)
    push_sent = models.IntegerField(default=0)
    in_app_sent = models.IntegerField(default=0)
    email_delivered = models.IntegerField(default=0)
    sms_delivered = models.IntegerField(default=0)
    push_delivered = models.IntegerField(default=0)
    total_read = models.IntegerField(default=0)
    click_through_rate = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Notification Analytics'
    
    def __str__(self):
        return f"Analytics for {self.date}"