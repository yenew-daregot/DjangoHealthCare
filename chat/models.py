from django.db import models
from django.utils import timezone
from patients.models import Patient
from doctors.models import Doctor
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatRoom(models.Model):
    ROOM_TYPES = (
        ('consultation', 'Consultation'),
        ('follow_up', 'Follow-up'),
        ('emergency', 'Emergency'),
        ('general', 'General Inquiry'),
        ('group', 'Group Chat'),
    )
    
    ROOM_STATUS = (
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('closed', 'Closed'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='consultation')
    status = models.CharField(max_length=20, choices=ROOM_STATUS, default='active')
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_encrypted = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # Healthcare specific fields
    related_appointment = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=10, choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')], default='normal')
    
    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['patient', 'doctor']),
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['-last_activity']),
        ]
    
    def __str__(self):
        return f"Chat: {self.patient} & {self.doctor} - {self.room_type}"
    
    def save(self, *args, **kwargs):
        if not self.title:
            self.title = f"Consultation between {self.patient} and {self.doctor}"
        super().save(*args, **kwargs)
    
    @property
    def unread_count_for_patient(self):
        return self.messages.filter(is_read=False).exclude(sender=self.patient.user).count()
    
    @property
    def unread_count_for_doctor(self):
        return self.messages.filter(is_read=False).exclude(sender=self.doctor.user).count()
    
    @property
    def last_message(self):
        return self.messages.last()
    
    @property
    def participant_count(self):
        return self.participants.filter(is_active=True).count()

class Message(models.Model):
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('prescription', 'Prescription'),
        ('lab_result', 'Lab Result'),
        ('appointment', 'Appointment'),
        ('system', 'System Message'),
        ('emoji', 'Emoji'),
    )
    
    MESSAGE_STATUS = (
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    )
    
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField(blank=True)
    
    # File attachments
    file = models.FileField(upload_to='chat_files/%Y/%m/%d/', null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.IntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=100, blank=True)
    thumbnail = models.ImageField(upload_to='chat_thumbnails/%Y/%m/%d/', null=True, blank=True)
    
    # Message metadata
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Healthcare specific fields
    related_prescription = models.ForeignKey('prescriptions.Prescription', on_delete=models.SET_NULL, null=True, blank=True)
    related_lab_result = models.ForeignKey('labs.LabRequest', on_delete=models.SET_NULL, null=True, blank=True)
    related_appointment = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Read status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    read_by = models.ManyToManyField(User, through='MessageReadStatus', related_name='read_messages')
    
    # Message status
    status = models.CharField(max_length=20, choices=MESSAGE_STATUS, default='sent')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Encryption
    is_encrypted = models.BooleanField(default=False)
    encryption_key = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['chat_room', 'timestamp']),
            models.Index(fields=['sender', 'timestamp']),
            models.Index(fields=['is_read', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender} at {self.timestamp}"
    
    def mark_as_read(self, user=None):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.status = 'read'
            self.save()
            
            if user:
                MessageReadStatus.objects.get_or_create(
                    message=self,
                    user=user,
                    defaults={'read_at': timezone.now()}
                )
    
    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.content = "This message was deleted"
        self.save()

class MessageReadStatus(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']

class ChatParticipant(models.Model):
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
    )
    
    PERMISSION_CHOICES = (
        ('read', 'Read Only'),
        ('write', 'Read & Write'),
        ('admin', 'Admin'),
    )
    
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    permissions = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='write')
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_online = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_typing = models.BooleanField(default=False)
    typing_updated_at = models.DateTimeField(null=True, blank=True)
    
    # Notification preferences
    notifications_enabled = models.BooleanField(default=True)
    sound_enabled = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['chat_room', 'user']
        indexes = [
            models.Index(fields=['chat_room', 'is_active']),
            models.Index(fields=['user', 'is_online']),
        ]
    
    def __str__(self):
        return f"{self.user} in {self.chat_room}"

class ChatNotification(models.Model):
    NOTIFICATION_TYPES = (
        ('new_message', 'New Message'),
        ('room_created', 'Chat Room Created'),
        ('participant_joined', 'Participant Joined'),
        ('participant_left', 'Participant Left'),
        ('file_shared', 'File Shared'),
        ('prescription_shared', 'Prescription Shared'),
        ('lab_result_shared', 'Lab Result Shared'),
        ('appointment_shared', 'Appointment Shared'),
        ('room_archived', 'Room Archived'),
        ('room_closed', 'Room Closed'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200, default='Notification')
    content = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    is_pushed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Notification for {self.user}: {self.notification_type}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

class ChatSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chat_settings')
    
    # General settings
    theme = models.CharField(max_length=20, choices=[('light', 'Light'), ('dark', 'Dark'), ('auto', 'Auto')], default='light')
    font_size = models.CharField(max_length=10, choices=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')], default='medium')
    
    # Notification settings
    desktop_notifications = models.BooleanField(default=True)
    sound_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    
    # Privacy settings
    read_receipts = models.BooleanField(default=True)
    typing_indicators = models.BooleanField(default=True)
    last_seen = models.BooleanField(default=True)
    
    # Auto settings
    auto_download_media = models.BooleanField(default=True)
    auto_play_videos = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Chat settings for {self.user}"

class ChatAnalytics(models.Model):
    chat_room = models.OneToOneField(ChatRoom, on_delete=models.CASCADE, related_name='analytics')
    
    # Message statistics
    total_messages = models.IntegerField(default=0)
    messages_by_patient = models.IntegerField(default=0)
    messages_by_doctor = models.IntegerField(default=0)
    
    # File statistics
    total_files = models.IntegerField(default=0)
    total_file_size = models.BigIntegerField(default=0)
    
    # Activity statistics
    average_response_time = models.DurationField(null=True, blank=True)
    peak_activity_hour = models.IntegerField(null=True, blank=True)
    
    # Session statistics
    total_sessions = models.IntegerField(default=0)
    average_session_duration = models.DurationField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analytics for {self.chat_room}"