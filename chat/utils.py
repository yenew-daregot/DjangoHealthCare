import os
from django.utils import timezone
from datetime import timedelta

def get_file_upload_path(instance, filename):
    """Generate upload path for chat files"""
    date_str = timezone.now().strftime('%Y/%m/%d')
    return f'chat_files/{date_str}/{filename}'

def is_file_safe(file):
    """Check if file is safe to upload"""
    # Check file extension
    safe_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx']
    ext = os.path.splitext(file.name)[1].lower()
    return ext in safe_extensions

def get_chat_room_stats(chat_room):
    """Get statistics for a chat room"""
    stats = {
        'total_messages': chat_room.messages.count(),
        'unread_messages': chat_room.messages.filter(is_read=False).count(),
        'participants_count': chat_room.participants.count(),
        'last_activity': chat_room.last_activity,
        'duration_days': (timezone.now() - chat_room.created_at).days
    }
    return stats

def cleanup_old_chat_files(days=30):
    """Clean up old chat files"""
    from .models import Message
    cutoff_date = timezone.now() - timedelta(days=days)
    
    old_messages = Message.objects.filter(
        timestamp__lt=cutoff_date,
        file__isnull=False
    )
    
    for message in old_messages:
        if message.file:
            try:
                message.file.delete(save=False)
            except:
                pass  # File might already be deleted
    
    return old_messages.count()

def send_chat_notification(chat_room, message, notification_type='new_message'):
    """Send notification to chat participants"""
    from .models import ChatNotification
    
    participants = chat_room.participants.exclude(user=message.sender)
    
    for participant in participants:
        ChatNotification.objects.create(
            user=participant.user,
            chat_room=chat_room,
            notification_type=notification_type,
            message=message
        )