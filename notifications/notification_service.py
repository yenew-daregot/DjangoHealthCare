import os
import logging
import threading
from typing import Dict, List, Optional, Any, Set, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from django.conf import settings
from django.core.mail import send_mail, send_mass_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.cache import cache
from django.apps import apps
import requests
import json

# Configure logging
logger = logging.getLogger(__name__)

# Service availability tracking
REQUIREMENTS = {
    'twilio': False,
    'firebase_admin': False,
    'phonenumbers': False
}

# Try to import optional dependencies with better error handling
twilio_client = None
TWILIO_ENABLED = False
TWILIO_ACCOUNT_SID = None
TWILIO_AUTH_TOKEN = None
TWILIO_PHONE_NUMBER = None

try:
    import twilio
    from twilio.rest import Client
    REQUIREMENTS['twilio'] = True
    
    TWILIO_ACCOUNT_SID = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    TWILIO_AUTH_TOKEN = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    TWILIO_PHONE_NUMBER = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
    
    if all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        TWILIO_ENABLED = True
        logger.info("Twilio SMS service initialized successfully")
    else:
        logger.warning("Twilio credentials not fully configured. SMS notifications disabled.")
        
except ImportError as e:
    logger.warning(f"Twilio not installed. SMS notifications disabled: {e}")

# Firebase configuration with better import handling
firebase_admin = None
messaging = None
FIREBASE_ENABLED = False

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    REQUIREMENTS['firebase_admin'] = True
    
    FIREBASE_CREDENTIALS_PATH = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
    if FIREBASE_CREDENTIALS_PATH and os.path.exists(FIREBASE_CREDENTIALS_PATH):
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
        FIREBASE_ENABLED = True
        logger.info("Firebase push notification service initialized successfully")
    else:
        logger.warning("Firebase credentials not configured or file not found. Push notifications disabled.")
        
except ImportError as e:
    logger.warning(f"Firebase Admin SDK not installed. Push notifications disabled: {e}")
except Exception as e:
    logger.error(f"Error initializing Firebase: {e}")

# Phone number handling
try:
    import phonenumbers
    REQUIREMENTS['phonenumbers'] = True
except ImportError:
    logger.warning("phonenumbers library not installed. Limited phone number validation available.")


class NotificationType(Enum):
    """Enum for notification types"""
    INFO = 'info'
    SUCCESS = 'success'
    WARNING = 'warning'
    ERROR = 'error'
    URGENT = 'urgent'
    EMERGENCY = 'emergency'


class Channel(Enum):
    """Enum for notification channels"""
    SMS = 'sms'
    PUSH = 'push'
    EMAIL = 'email'
    IN_APP = 'in_app'


@dataclass
class NotificationResult:
    """Data class for notification results"""
    channel: str
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    max_requests: int
    time_window: int  # in seconds
    cache_prefix: str


class NotificationService:
    """
    Comprehensive notification service supporting multiple channels:
    - SMS via Twilio
    - Push notifications via Firebase
    - Email via Django
    - In-app notifications
    
    Thread-safe and configurable with rate limiting
    """
    
    # Thread lock for thread safety
    _lock = threading.RLock()
    
    # Rate limiting configuration
    RATE_LIMITS = {
        'sms': RateLimitConfig(max_requests=5, time_window=3600, cache_prefix='sms_rate_limit'),
        'push': RateLimitConfig(max_requests=10, time_window=3600, cache_prefix='push_rate_limit'),
        'email': RateLimitConfig(max_requests=20, time_window=3600, cache_prefix='email_rate_limit'),
    }
    
    # Channel configurations from settings
    URGENT_CHANNELS = getattr(settings, 'NOTIFICATION_URGENT_CHANNELS', ['sms', 'push', 'email', 'in_app'])
    WARNING_CHANNELS = getattr(settings, 'NOTIFICATION_WARNING_CHANNELS', ['push', 'email', 'in_app'])
    DEFAULT_CHANNELS = getattr(settings, 'NOTIFICATION_DEFAULT_CHANNELS', ['in_app'])
    
    def __init__(self):
        self.enabled_services = {
            Channel.SMS.value: TWILIO_ENABLED,
            Channel.PUSH.value: FIREBASE_ENABLED,
            Channel.EMAIL.value: True,  # Always available with Django
            Channel.IN_APP.value: True
        }
        
        self._template_cache = {}
        
    def check_rate_limit(self, user_id: int, channel: str) -> bool:
        """
        Check if rate limit is exceeded for a user and channel
        
        Args:
            user_id: User ID
            channel: Notification channel
            
        Returns:
            True if allowed, False if rate limited
        """
        if channel not in self.RATE_LIMITS:
            return True
            
        config = self.RATE_LIMITS[channel]
        cache_key = f"{config.cache_prefix}_{user_id}"
        
        with self._lock:
            request_count = cache.get(cache_key, 0)
            if request_count >= config.max_requests:
                logger.warning(f"Rate limit exceeded for user {user_id} on channel {channel}")
                return False
            
            # Increment counter
            cache.set(cache_key, request_count + 1, timeout=config.time_window)
            return True
    
    def reset_rate_limit(self, user_id: int, channel: str) -> None:
        """Reset rate limit for a user and channel"""
        if channel in self.RATE_LIMITS:
            config = self.RATE_LIMITS[channel]
            cache_key = f"{config.cache_prefix}_{user_id}"
            cache.delete(cache_key)
    
    def send_notification(self, 
                         user, 
                         title: str, 
                         message: str, 
                         notification_type: Union[str, NotificationType] = NotificationType.INFO.value,
                         channels: Optional[List[str]] = None,
                         data: Optional[Dict[str, Any]] = None,
                         template_context: Optional[Dict[str, Any]] = None) -> Dict[str, NotificationResult]:
        """
        Send notification through multiple channels
        
        Args:
            user: User object with id, email, phone_number, fcm_token attributes
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, success, warning, error, urgent, emergency)
            channels: List of channels to use ['sms', 'push', 'email', 'in_app']
            data: Additional data for the notification
            template_context: Additional context for email templates
            
        Returns:
            Dict with NotificationResult for each channel
        """
        if channels is None:
            channels = self.DEFAULT_CHANNELS.copy()
            
        # Convert string notification_type to enum value
        if isinstance(notification_type, str):
            try:
                notification_type = NotificationType(notification_type).value
            except ValueError:
                notification_type = NotificationType.INFO.value
                logger.warning(f"Invalid notification type: {notification_type}, defaulting to INFO")
        
        # Auto-select channels based on notification type
        if notification_type in [NotificationType.URGENT.value, NotificationType.EMERGENCY.value]:
            channels = self.URGENT_CHANNELS.copy()
        elif notification_type in [NotificationType.WARNING.value, NotificationType.ERROR.value]:
            channels = self.WARNING_CHANNELS.copy()
            # Ensure we don't duplicate channels
            for channel in channels:
                if channel not in self.WARNING_CHANNELS:
                    self.WARNING_CHANNELS.append(channel)
        
        results = {}
        
        for channel in set(channels):  # Use set to avoid duplicates
            try:
                # Check if channel is enabled
                if not self.enabled_services.get(channel, False):
                    results[channel] = NotificationResult(
                        channel=channel,
                        success=False,
                        error=f"Channel {channel} not available or disabled"
                    )
                    continue
                
                # Check rate limit
                if not self.check_rate_limit(user.id, channel):
                    results[channel] = NotificationResult(
                        channel=channel,
                        success=False,
                        error=f"Rate limit exceeded for channel {channel}"
                    )
                    continue
                
                # Send notification based on channel
                if channel == Channel.SMS.value:
                    result = self._send_sms(user, message, data)
                elif channel == Channel.PUSH.value:
                    result = self._send_push_notification(user, title, message, data)
                elif channel == Channel.EMAIL.value:
                    result = self._send_email(user, title, message, data, template_context)
                elif channel == Channel.IN_APP.value:
                    result = self._create_in_app_notification(user, title, message, notification_type, data)
                else:
                    result = NotificationResult(
                        channel=channel,
                        success=False,
                        error=f"Unknown channel: {channel}"
                    )
                
                results[channel] = result
                    
            except Exception as e:
                logger.error(f"Error sending {channel} notification to user {user.id}: {e}")
                results[channel] = NotificationResult(
                    channel=channel,
                    success=False,
                    error=str(e)
                )
                
        return results
    
    def _send_sms(self, user, message: str, data: Optional[Dict] = None) -> NotificationResult:
        """Send SMS notification via Twilio"""
        if not TWILIO_ENABLED:
            return NotificationResult(
                channel=Channel.SMS.value,
                success=False,
                error="Twilio service not enabled"
            )
            
        try:
            # Get user phone number
            phone_number = getattr(user, 'phone_number', None)
            if not phone_number:
                return NotificationResult(
                    channel=Channel.SMS.value,
                    success=False,
                    error=f"No phone number for user {user.id}"
                )
            
            # Format and validate phone number
            formatted_number = self._format_phone_number(phone_number)
            if not formatted_number:
                return NotificationResult(
                    channel=Channel.SMS.value,
                    success=False,
                    error=f"Invalid phone number format for user {user.id}: {phone_number}"
                )
            
            # Truncate message if too long for SMS
            if len(message) > 1600:  # Twilio limit is 1600 chars
                message = message[:1597] + "..."
            
            # Send SMS
            message_obj = twilio_client.messages.create(
                body=message,
                from_=TWILIO_PHONE_NUMBER,
                to=formatted_number
            )
            
            logger.info(f"SMS sent successfully to {formatted_number}: {message_obj.sid}")
            return NotificationResult(
                channel=Channel.SMS.value,
                success=True,
                message_id=message_obj.sid
            )
            
        except Exception as e:
            logger.error(f"Failed to send SMS to user {user.id}: {e}")
            return NotificationResult(
                channel=Channel.SMS.value,
                success=False,
                error=str(e)
            )
    
    def _format_phone_number(self, phone_number: str) -> Optional[str]:
        """Format phone number to E.164 format"""
        if not phone_number:
            return None
        
        # If phonenumbers library is available, use it
        if REQUIREMENTS['phonenumbers']:
            try:
                # Try to parse with default region or detect it
                parsed = phonenumbers.parse(phone_number, None)
                if phonenumbers.is_valid_number(parsed):
                    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                else:
                    logger.warning(f"Invalid phone number detected: {phone_number}")
                    return None
            except phonenumbers.NumberParseException:
                # Fall back to simple formatting
                pass
        
        # Simple formatting fallback
        phone_number = phone_number.strip()
        
        # Remove all non-numeric characters except '+'
        if phone_number.startswith('+'):
            cleaned = '+' + ''.join(filter(str.isdigit, phone_number[1:]))
        else:
            cleaned = ''.join(filter(str.isdigit, phone_number))
            # Assume US number if no country code
            if len(cleaned) == 10:
                cleaned = '+1' + cleaned
        
        return cleaned if cleaned.startswith('+') and len(cleaned) > 7 else None
    
    def _send_push_notification(self, user, title: str, message: str, 
                               data: Optional[Dict] = None) -> NotificationResult:
        """Send push notification via Firebase"""
        if not FIREBASE_ENABLED:
            return NotificationResult(
                channel=Channel.PUSH.value,
                success=False,
                error="Firebase service not enabled"
            )
            
        try:
            # Get user's FCM token
            fcm_token = getattr(user, 'fcm_token', None)
            if not fcm_token:
                return NotificationResult(
                    channel=Channel.PUSH.value,
                    success=False,
                    error=f"No FCM token for user {user.id}"
                )
            
            # Prepare notification data
            notification_data = {
                'title': title,
                'body': message,
                'timestamp': datetime.now().isoformat(),
                'user_id': str(user.id)
            }
            
            if data:
                notification_data.update(data)
            
            # Create notification
            notification = messaging.Notification(
                title=title[:100],  # Firebase title limit
                body=message[:255]  # Firebase body limit
            )
            
            # Create message
            push_message = messaging.Message(
                notification=notification,
                data=notification_data,
                token=fcm_token
            )
            
            # Send message
            response = messaging.send(push_message)
            logger.info(f"Push notification sent successfully to user {user.id}: {response}")
            
            return NotificationResult(
                channel=Channel.PUSH.value,
                success=True,
                message_id=response
            )
            
        except Exception as e:
            logger.error(f"Failed to send push notification to user {user.id}: {e}")
            return NotificationResult(
                channel=Channel.PUSH.value,
                success=False,
                error=str(e)
            )
    
    def _send_email(self, user, title: str, message: str, data: Optional[Dict] = None,
                   template_context: Optional[Dict] = None) -> NotificationResult:
        """Send email notification"""
        try:
            # Check if user has email
            if not hasattr(user, 'email') or not user.email:
                return NotificationResult(
                    channel=Channel.EMAIL.value,
                    success=False,
                    error=f"No email address for user {user.id}"
                )
            
            # Prepare email context
            context = {
                'user': user,
                'title': title,
                'message': message,
                'data': data or {},
                'site_name': getattr(settings, 'SITE_NAME', 'Healthcare System'),
                'timestamp': datetime.now(),
                'unsubscribe_url': getattr(settings, 'UNSUBSCRIBE_URL', '#'),
            }
            
            if template_context:
                context.update(template_context)
            
            # Get email templates from settings or use defaults
            html_template = getattr(settings, 'NOTIFICATION_HTML_TEMPLATE', 
                                   'notifications/email_notification.html')
            text_template = getattr(settings, 'NOTIFICATION_TEXT_TEMPLATE', 
                                   'notifications/email_notification.txt')
            
            # Render email content with fallback
            try:
                html_message = render_to_string(html_template, context)
            except Exception as e:
                logger.warning(f"HTML template not found, using plain text: {e}")
                html_message = None
                
            try:
                plain_message = render_to_string(text_template, context)
            except Exception as e:
                logger.warning(f"Text template not found, using stripped HTML: {e}")
                plain_message = strip_tags(html_message) if html_message else message
            
            # If no HTML message, create a simple one
            if not html_message:
                html_message = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{title}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                        .content {{ margin: 20px 0; }}
                        .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>{title}</h1>
                        </div>
                        <div class="content">
                            <p>{message}</p>
                        </div>
                        <div class="footer">
                            <p>This is an automated message from {context['site_name']}.</p>
                            <p><a href="{context['unsubscribe_url']}">Unsubscribe from notifications</a></p>
                        </div>
                    </div>
                </body>
                </html>
                """
            
            # Send email
            send_mail(
                subject=title[:255],  # Email subject length limit
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Email sent successfully to {user.email}")
            return NotificationResult(
                channel=Channel.EMAIL.value,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Failed to send email to user {user.id}: {e}")
            return NotificationResult(
                channel=Channel.EMAIL.value,
                success=False,
                error=str(e)
            )
    
    def _create_in_app_notification(self, user, title: str, message: str, 
                                  notification_type: str, data: Optional[Dict] = None) -> NotificationResult:
        """Create in-app notification without circular imports"""
        try:
            # Use Django's app registry to avoid circular imports
            try:
                Notification = apps.get_model('notifications', 'Notification')
            except LookupError:
                # Try alternative app names
                try:
                    Notification = apps.get_model('core', 'Notification')
                except LookupError:
                    try:
                        Notification = apps.get_model('users', 'Notification')
                    except LookupError:
                        # If no Notification model exists, log and return success
                        logger.warning("Notification model not found in any app. In-app notifications disabled.")
                        return NotificationResult(
                            channel=Channel.IN_APP.value,
                            success=False,
                            error="Notification model not found"
                        )
            
            # Create notification
            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                metadata=data or {},
                is_read=False,
                created_at=datetime.now()
            )
            
            logger.info(f"In-app notification created for user {user.id}: {notification.id}")
            return NotificationResult(
                channel=Channel.IN_APP.value,
                success=True,
                message_id=str(notification.id)
            )
            
        except Exception as e:
            logger.error(f"Failed to create in-app notification for user {user.id}: {e}")
            return NotificationResult(
                channel=Channel.IN_APP.value,
                success=False,
                error=str(e)
            )
    
    def send_bulk_notifications(self, users, title: str, message: str,
                               notification_type: str = NotificationType.INFO.value,
                               channels: Optional[List[str]] = None,
                               batch_size: int = 50) -> Dict[int, Dict[str, NotificationResult]]:
        """
        Send notifications to multiple users efficiently
        
        Args:
            users: QuerySet or list of users
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            channels: List of channels to use
            batch_size: Number of users to process at once
            
        Returns:
            Dict mapping user_id to notification results
        """
        results = {}
        
        for i in range(0, len(users), batch_size):
            batch = users[i:i + batch_size]
            for user in batch:
                user_results = self.send_notification(
                    user=user,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    channels=channels
                )
                results[user.id] = user_results
        
        return results
    
    # Healthcare-specific notification methods with improved error handling
    
    def notify_appointment_created(self, appointment) -> Dict[str, Dict[str, NotificationResult]]:
        """Notify about new appointment with detailed results"""
        try:
            patient = appointment.patient.user
            doctor = appointment.doctor.user
            
            # Format appointment time
            appointment_time = appointment.appointment_time.strftime('%I:%M %p') if hasattr(appointment.appointment_time, 'strftime') else str(appointment.appointment_time)
            appointment_date = appointment.appointment_date.strftime('%B %d, %Y') if hasattr(appointment.appointment_date, 'strftime') else str(appointment.appointment_date)
            
            results = {}
            
            # Notify patient
            patient_message = f"Your appointment with Dr. {doctor.first_name} {doctor.last_name} has been scheduled for {appointment_date} at {appointment_time}"
            patient_results = self.send_notification(
                user=patient,
                title="Appointment Scheduled",
                message=patient_message,
                notification_type=NotificationType.INFO.value,
                channels=['push', 'email', 'in_app'],
                data={
                    'appointment_id': appointment.id,
                    'type': 'appointment_created',
                    'appointment_date': appointment_date,
                    'appointment_time': appointment_time,
                    'doctor_name': f"Dr. {doctor.first_name} {doctor.last_name}"
                }
            )
            results['patient'] = patient_results
            
            # Notify doctor
            doctor_message = f"New appointment scheduled with {patient.first_name} {patient.last_name} on {appointment_date} at {appointment_time}"
            doctor_results = self.send_notification(
                user=doctor,
                title="New Appointment",
                message=doctor_message,
                notification_type=NotificationType.INFO.value,
                channels=['push', 'in_app'],
                data={
                    'appointment_id': appointment.id,
                    'type': 'appointment_created',
                    'appointment_date': appointment_date,
                    'appointment_time': appointment_time,
                    'patient_name': f"{patient.first_name} {patient.last_name}"
                }
            )
            results['doctor'] = doctor_results
            
            return results
            
        except Exception as e:
            logger.error(f"Error sending appointment created notifications: {e}")
            return {'error': str(e)}
    
    def notify_appointment_reminder(self, appointment, hours_before: int = 1) -> Dict[str, NotificationResult]:
        """Send appointment reminder"""
        try:
            patient = appointment.patient.user
            
            # Format appointment time
            appointment_time = appointment.appointment_time.strftime('%I:%M %p') if hasattr(appointment.appointment_time, 'strftime') else str(appointment.appointment_time)
            
            message = f"Reminder: You have an appointment in {hours_before} hour(s) at {appointment_time}"
            
            return self.send_notification(
                user=patient,
                title="Appointment Reminder",
                message=message,
                notification_type=NotificationType.WARNING.value,
                channels=['sms', 'push', 'in_app'],
                data={
                    'appointment_id': appointment.id,
                    'type': 'appointment_reminder',
                    'hours_before': hours_before,
                    'appointment_time': appointment_time
                }
            )
            
        except Exception as e:
            logger.error(f"Error sending appointment reminder: {e}")
            return {'error': str(e)}
    
    def notify_health_alert(self, vital_reading) -> Dict[str, Dict[str, NotificationResult]]:
        """Notify about abnormal health readings"""
        try:
            patient = vital_reading.patient.user
            doctor = vital_reading.doctor.user if vital_reading.doctor else None
            
            vital_type = getattr(vital_reading, 'get_vital_type_display', 
                               lambda: getattr(vital_reading, 'vital_type', 'Unknown'))()
            
            message = f"Alert: Abnormal {vital_type} reading detected - {vital_reading.value} {vital_reading.unit}"
            
            results = {}
            
            # Notify patient
            patient_results = self.send_notification(
                user=patient,
                title="Health Alert",
                message=message,
                notification_type=NotificationType.URGENT.value,
                channels=['sms', 'push', 'email', 'in_app'],
                data={
                    'vital_reading_id': vital_reading.id,
                    'type': 'health_alert',
                    'vital_type': vital_type,
                    'value': vital_reading.value,
                    'unit': vital_reading.unit,
                    'timestamp': vital_reading.recorded_at.isoformat() if hasattr(vital_reading, 'recorded_at') else datetime.now().isoformat()
                }
            )
            results['patient'] = patient_results
            
            # Notify doctor if assigned
            if doctor:
                doctor_message = f"Patient {patient.first_name} {patient.last_name}: {message}"
                doctor_results = self.send_notification(
                    user=doctor,
                    title="Patient Health Alert",
                    message=doctor_message,
                    notification_type=NotificationType.URGENT.value,
                    channels=['sms', 'push', 'in_app'],
                    data={
                        'vital_reading_id': vital_reading.id,
                        'patient_id': vital_reading.patient.id,
                        'type': 'health_alert',
                        'patient_name': f"{patient.first_name} {patient.last_name}",
                        'vital_type': vital_type,
                        'value': vital_reading.value,
                        'unit': vital_reading.unit
                    }
                )
                results['doctor'] = doctor_results
            
            return results
            
        except Exception as e:
            logger.error(f"Error sending health alert notifications: {e}")
            return {'error': str(e)}
    
    def notify_emergency_request(self, emergency_request, batch_size: int = 10) -> Dict[str, Dict[str, NotificationResult]]:
        """Notify about emergency requests with batching for performance"""
        try:
            patient = emergency_request.patient.user
            
            # Get emergency staff using a more efficient query
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            emergency_staff = User.objects.filter(
                is_active=True,
                role__in=['DOCTOR', 'ADMIN', 'EMERGENCY_RESPONDER']
            ).select_related('doctor_profile').only('id', 'email', 'phone_number', 'fcm_token', 'first_name', 'last_name', 'role')
            
            results = {}
            
            # Notify patient
            patient_message = f"Emergency assistance has been requested. Help is on the way."
            patient_results = self.send_notification(
                user=patient,
                title="Emergency Request Sent",
                message=patient_message,
                notification_type=NotificationType.EMERGENCY.value,
                channels=['sms', 'push', 'in_app'],
                data={
                    'emergency_request_id': emergency_request.id,
                    'type': 'emergency_request_sent',
                    'location': emergency_request.location,
                    'timestamp': datetime.now().isoformat()
                }
            )
            results['patient'] = patient_results
            
            # Notify staff in batches
            staff_message = f"EMERGENCY: {patient.first_name} {patient.last_name} needs immediate assistance. Location: {emergency_request.location}"
            
            staff_results = self.send_bulk_notifications(
                users=emergency_staff,
                title="EMERGENCY REQUEST",
                message=staff_message,
                notification_type=NotificationType.EMERGENCY.value,
                channels=['sms', 'push', 'in_app'],
                batch_size=batch_size
            )
            results['staff'] = staff_results
            
            return results
            
        except Exception as e:
            logger.error(f"Error sending emergency request notifications: {e}")
            return {'error': str(e)}
    
    def notify_prescription_ready(self, prescription) -> Dict[str, NotificationResult]:
        """Notify when prescription is ready"""
        try:
            patient = prescription.patient.user
            
            message = f"Your prescription for {prescription.medication_name} is ready for pickup"
            
            return self.send_notification(
                user=patient,
                title="Prescription Ready",
                message=message,
                notification_type=NotificationType.INFO.value,
                channels=['sms', 'push', 'in_app'],
                data={
                    'prescription_id': prescription.id,
                    'type': 'prescription_ready',
                    'medication_name': prescription.medication_name,
                    'pharmacy': getattr(prescription, 'pharmacy', 'Your pharmacy'),
                    'ready_by': getattr(prescription, 'ready_by', None)
                }
            )
            
        except Exception as e:
            logger.error(f"Error sending prescription ready notification: {e}")
            return {'error': str(e)}
    
    def notify_lab_results_available(self, lab_result) -> Dict[str, NotificationResult]:
        """Notify when lab results are available"""
        try:
            patient = lab_result.patient.user
            
            message = f"Your lab results for {lab_result.test_name} are now available"
            
            return self.send_notification(
                user=patient,
                title="Lab Results Available",
                message=message,
                notification_type=NotificationType.INFO.value,
                channels=['push', 'email', 'in_app'],
                data={
                    'lab_result_id': lab_result.id,
                    'type': 'lab_results_available',
                    'test_name': lab_result.test_name,
                    'test_date': lab_result.test_date.isoformat() if hasattr(lab_result, 'test_date') else None,
                    'doctor_notes': getattr(lab_result, 'doctor_notes', '')
                }
            )
            
        except Exception as e:
            logger.error(f"Error sending lab results notification: {e}")
            return {'error': str(e)}
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get detailed status of all notification services"""
        status = {
            'services': self.enabled_services.copy(),
            'requirements': REQUIREMENTS,
            'configuration': {
                'twilio_configured': all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]),
                'firebase_configured': FIREBASE_ENABLED,
                'urgent_channels': self.URGENT_CHANNELS,
                'warning_channels': self.WARNING_CHANNELS,
                'default_channels': self.DEFAULT_CHANNELS
            }
        }
        
        return status
    
    def test_service(self, channel: str, user) -> NotificationResult:
        """
        Test a specific notification channel
        
        Args:
            channel: Channel to test
            user: User to send test notification to
            
        Returns:
            NotificationResult with test outcome
        """
        test_messages = {
            'sms': "Test SMS notification from Healthcare System",
            'push': "Test push notification from Healthcare System",
            'email': "Test email notification from Healthcare System",
            'in_app': "Test in-app notification from Healthcare System"
        }
        
        message = test_messages.get(channel, "Test notification")
        
        return self.send_notification(
            user=user,
            title=f"Test {channel.upper()} Notification",
            message=message,
            notification_type=NotificationType.INFO.value,
            channels=[channel]
        ).get(channel, NotificationResult(channel=channel, success=False, error="Channel not found in results"))


# Factory function instead of singleton for better testability
@lru_cache(maxsize=1)
def get_notification_service() -> NotificationService:
    """Get or create a notification service instance (cached)"""
    return NotificationService()


# Create a single instance for convenience
notification_service = get_notification_service()


# Convenience functions
def send_notification(*args, **kwargs):
    """Convenience function to send notification"""
    service = get_notification_service()
    return service.send_notification(*args, **kwargs)

def notify_appointment_created(appointment):
    """Convenience function for appointment notifications"""
    service = get_notification_service()
    return service.notify_appointment_created(appointment)

def notify_health_alert(vital_reading):
    """Convenience function for health alerts"""
    service = get_notification_service()
    return service.notify_health_alert(vital_reading)

def notify_emergency_request(emergency_request):
    """Convenience function for emergency notifications"""
    service = get_notification_service()
    return service.notify_emergency_request(emergency_request)

def get_service_status():
    """Get notification service status"""
    service = get_notification_service()
    return service.get_service_status()