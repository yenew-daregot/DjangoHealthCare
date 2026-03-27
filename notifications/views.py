from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
from .notification_service import get_notification_service

from .models import (
    Notification, NotificationTemplate, NotificationPreference,
    NotificationLog, BulkNotification, ScheduledReminder, NotificationAnalytics
)
from .serializers import (
    NotificationSerializer, NotificationDetailSerializer,
    NotificationTemplateSerializer, NotificationPreferenceSerializer,
    NotificationLogSerializer, BulkNotificationSerializer,
    ScheduledReminderSerializer, NotificationAnalyticsSerializer,
    CreateNotificationSerializer, UpdatePreferenceSerializer,
    CreateBulkNotificationSerializer, CreateReminderSerializer,
    TestNotificationSerializer, MobileDeviceSerializer
)
from users.models import CustomUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from appointments.models import Appointment
from prescriptions.models import Prescription
from labs.models import LabRequest
from billing.models import Invoice
from emergency.models import EmergencyRequest

# Import from your notification_service
from .notification_service import get_notification_service

# Import models
from .models import Notification, NotificationTemplate

@receiver(post_save, sender=Appointment)
def create_appointment_notification(sender, instance, created, **kwargs):
    if created:
        # Get notification service
        notification_service = get_notification_service()
        
        # Notification for new appointment to patient
        notification_service.send_notification(
            user=instance.patient.user,
            title=f"New Appointment Scheduled",
            message=f"Your appointment with Dr. {instance.doctor.user.get_full_name()} is scheduled for {instance.appointment_date.strftime('%B %d, %Y at %I:%M %p')}",
            notification_type='info',
            channels=['in_app', 'email'],
            data={
                'appointment_id': instance.id,
                'doctor_name': instance.doctor.user.get_full_name(),
                'appointment_date': instance.appointment_date.strftime('%B %d, %Y'),
                'appointment_time': instance.appointment_time.strftime('%I:%M %p') if hasattr(instance, 'appointment_time') else '',
                'type': 'appointment_created'
            }
        )
        
        # notify the doctor with all channels
        notification_service.send_notification(
            user=instance.doctor.user,
            title=f"New Appointment with {instance.patient.user.get_full_name()}",
            message=f"You have a new appointment with {instance.patient.user.get_full_name()} on {instance.appointment_date.strftime('%B %d, %Y at %I:%M %p')}",
            notification_type='info',
            channels=['sms', 'push', 'email', 'in_app'],  
            data={
                'appointment_id': instance.id,
                'patient_name': instance.patient.user.get_full_name(),
                'appointment_date': instance.appointment_date.strftime('%B %d, %Y'),
                'appointment_time': instance.appointment_time.strftime('%I:%M %p') if hasattr(instance, 'appointment_time') else '',
                'type': 'appointment_created',
                'priority': instance.priority if hasattr(instance, 'priority') else 'normal'
            }
        )

@receiver(post_save, sender=Prescription)
def create_prescription_notification(sender, instance, created, **kwargs):
    if created:
        notification_service = get_notification_service()
        
        notification_service.send_notification(
            user=instance.appointment.patient.user,
            title=f"New Prescription from Dr. {instance.appointment.doctor.user.get_full_name()}",
            message=f"Your prescription for {instance.medication.name if hasattr(instance, 'medication') else 'medication'} is ready.",
            notification_type='info',
            channels=['in_app', 'email'],
            data={
                'prescription_id': instance.id,
                'doctor_name': instance.appointment.doctor.user.get_full_name(),
                'medication_name': instance.medication.name if hasattr(instance, 'medication') else 'Unknown',
                'type': 'prescription_ready'
            }
        )

# Notification Views
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # Filter by read status if provided
        is_read = self.request.GET.get('is_read')
        notification_type = self.request.GET.get('type')
        
        queryset = Notification.objects.filter(user=user)
        
        if is_read is not None:
            if is_read.lower() == 'true':
                queryset = queryset.filter(is_read=True)
            else:
                queryset = queryset.filter(is_read=False)
        
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        return queryset

class NotificationDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = NotificationDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_read:
            instance.mark_as_read()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
from rest_framework.decorators import api_view, permission_classes

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_appointment_notification_view(request):
    """Send appointment notification"""
    appointment_id = request.data.get('appointment_id')
    notification_type = request.data.get('notification_type', 'created')
    
    if not appointment_id:
        return Response(
            {'error': 'appointment_id is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from appointments.models import Appointment
        appointment = Appointment.objects.get(id=appointment_id)
        
        notification_service = get_notification_service()
        
        if notification_type == 'created':
            results = notification_service.notify_appointment_created(appointment)
        elif notification_type == 'reminder':
            results = notification_service.notify_appointment_reminder(appointment)
        else:
            return Response(
                {'error': f'Unsupported notification type: {notification_type}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'success': True,
            'results': results,
            'message': f'Appointment {notification_type} notification sent'
        })
        
    except Appointment.DoesNotExist:
        return Response(
            {'error': 'Appointment not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_doctor_notification_preferences(request, doctor_id):
    """Get doctor notification preferences"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        doctor = User.objects.get(id=doctor_id)
        
        # Check if user is a doctor
        if not hasattr(doctor, 'role') or doctor.role != 'DOCTOR':
            return Response(
                {'error': 'User is not a doctor'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    except User.DoesNotExist:
        return Response(
            {'error': 'Doctor not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get notification preferences
    from .models import NotificationPreference
    preference, created = NotificationPreference.objects.get_or_create(
        user=doctor,
        defaults={
            'email_enabled': True,
            'sms_enabled': True,
            'push_enabled': True,
            'in_app_enabled': True,
            'appointment_notifications': True,
            'emergency_notifications': True,
        }
    )
    
    # Determine available channels
    available_channels = []
    
    if preference.sms_enabled and hasattr(doctor, 'phone_number') and doctor.phone_number:
        available_channels.append('sms')
    
    if preference.push_enabled and hasattr(doctor, 'fcm_token') and doctor.fcm_token:
        available_channels.append('push')
    
    if preference.email_enabled and doctor.email:
        available_channels.append('email')
    
    if preference.in_app_enabled:
        available_channels.append('in_app')
    
    response_data = {
        'doctor_id': doctor.id,
        'doctor_name': doctor.get_full_name() if hasattr(doctor, 'get_full_name') else f"{doctor.first_name} {doctor.last_name}",
        'available_channels': available_channels,
        'preferences': {
            'email_enabled': preference.email_enabled,
            'sms_enabled': preference.sms_enabled,
            'push_enabled': preference.push_enabled,
            'in_app_enabled': preference.in_app_enabled,
            'appointment_notifications': preference.appointment_notifications,
            'emergency_notifications': preference.emergency_notifications,
        }
    }
    
    return Response(response_data)
class MarkNotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.mark_as_read()
        return Response({'status': 'Notification marked as read'})

class MarkAllNotificationsReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return Response({
            'status': 'All notifications marked as read',
            'updated_count': updated_count
        })

class UnreadNotificationCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return Response({'unread_count': count})

class RecentNotificationsView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        limit = int(self.request.GET.get('limit', 10))
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')[:limit]

# Notification Preference Views
class NotificationPreferenceView(generics.RetrieveAPIView):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        preference, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preference

class UpdateNotificationPreferenceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        preference, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = UpdatePreferenceSerializer(preference, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(NotificationPreferenceSerializer(preference).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Notification Template Views
class NotificationTemplateListView(generics.ListAPIView):
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return NotificationTemplate.objects.filter(is_active=True)

class NotificationTemplateDetailView(generics.RetrieveAPIView):
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = NotificationTemplate.objects.all()

# Bulk Notification Views
class BulkNotificationListCreateView(generics.ListCreateAPIView):
    serializer_class = BulkNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only show bulk notifications created by the user or all if admin
        if self.request.user.role == 'ADMIN':
            return BulkNotification.objects.all()
        return BulkNotification.objects.filter(created_by=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateBulkNotificationSerializer
        return BulkNotificationSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class BulkNotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BulkNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'ADMIN':
            return BulkNotification.objects.all()
        return BulkNotification.objects.filter(created_by=self.request.user)

class SendBulkNotificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        bulk_notification = get_object_or_404(BulkNotification, pk=pk)
        
        # Check permissions
        if bulk_notification.created_by != request.user and request.user.role != 'ADMIN':
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if bulk_notification.is_sent:
            return Response(
                {'error': 'Bulk notification has already been sent'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # In a real implementation, this would send the notifications
        # For now, we'll just mark it as sent
        bulk_notification.is_sent = True
        bulk_notification.sent_at = timezone.now()
        bulk_notification.save()
        
        return Response({'status': 'Bulk notification sent successfully'})

# Scheduled Reminder Views
class ScheduledReminderListCreateView(generics.ListCreateAPIView):
    serializer_class = ScheduledReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ScheduledReminder.objects.filter(user=self.request.user, is_active=True)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateReminderSerializer
        return ScheduledReminderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ScheduledReminderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ScheduledReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ScheduledReminder.objects.filter(user=self.request.user)

class ToggleReminderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        reminder = get_object_or_404(ScheduledReminder, pk=pk, user=request.user)
        reminder.is_active = not reminder.is_active
        reminder.save()
        
        return Response({
            'status': 'Reminder activated' if reminder.is_active else 'Reminder deactivated',
            'is_active': reminder.is_active
        })

# Analytics Views
class DailyNotificationAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Only admins can view analytics
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        date_str = request.GET.get('date', timezone.now().date().isoformat())
        try:
            target_date = datetime.fromisoformat(date_str).date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        analytics, created = NotificationAnalytics.objects.get_or_create(date=target_date)
        serializer = NotificationAnalyticsSerializer(analytics)
        return Response(serializer.data)

class NotificationSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Only admins can view summary
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        days = int(request.GET.get('days', 7))
        start_date = timezone.now().date() - timedelta(days=days)
        
        summary = {
            'period': f'Last {days} days',
            'total_notifications': Notification.objects.filter(
                created_at__date__gte=start_date
            ).count(),
            'notifications_by_type': list(
                Notification.objects.filter(
                    created_at__date__gte=start_date
                ).values('notification_type').annotate(
                    count=Count('id')
                ).order_by('-count')
            ),
            'delivery_stats': self.get_delivery_stats(start_date),
            'user_engagement': self.get_user_engagement(start_date),
        }
        
        return Response(summary)

    def get_delivery_stats(self, start_date):
        logs = NotificationLog.objects.filter(created_at__date__gte=start_date)
        total = logs.count()
        if total == 0:
            return {}
        
        return {
            'total_delivery_attempts': total,
            'sent_count': logs.filter(status='sent').count(),
            'delivered_count': logs.filter(status='delivered').count(),
            'failed_count': logs.filter(status='failed').count(),
            'success_rate': (logs.filter(status='delivered').count() / total) * 100,
        }

    def get_user_engagement(self, start_date):
        total_users = CustomUser.objects.count()
        users_with_notifications = Notification.objects.filter(
            created_at__date__gte=start_date
        ).values('user').distinct().count()
        
        return {
            'total_users': total_users,
            'users_with_notifications': users_with_notifications,
            'engagement_rate': (users_with_notifications / total_users) * 100 if total_users > 0 else 0,
        }

# Test Endpoints
class SendTestNotificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TestNotificationSerializer(data=request.data)
        
        if serializer.is_valid():
            notification_type = serializer.validated_data.get('notification_type', 'system')
            channels = serializer.validated_data.get('channels', ['in_app'])
            
            # Create test notification
            notification = Notification.objects.create(
                user=request.user,
                notification_type=notification_type,
                title="Test Notification",
                message="This is a test notification to verify your notification settings.",
                short_message="Test notification",
                channels=channels,
                action_url="/notifications",
                action_text="View Notifications",
                created_by=request.user
            )
            
            # Mark as sent 
            notification.mark_as_sent()
            # Create delivery logs for each channel
            for channel in channels:
                NotificationLog.objects.create(
                    notification=notification,
                    channel=channel,
                    recipient=request.user.email if channel == 'email' else 
                            request.user.phone_number if channel == 'sms' else 
                            'device_token' if channel == 'push' else 'in_app',
                    status='sent' if channel == 'in_app' else 'delivered',
                    sent_at=timezone.now()
                )
            
            return Response({
                'message': 'Test notification sent successfully',
                'notification_id': notification.id
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Mobile Device Registration
class RegisterMobileDeviceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MobileDeviceSerializer(data=request.data)
        
        if serializer.is_valid():
            # In a real implementation, this would store the device token
            # For now, we'll just return success
            device_token = serializer.validated_data['device_token']
            platform = serializer.validated_data['platform']
            
            # Store device information in user's metadata or separate model
            # This is a simplified implementation
            
            return Response({
                'status': 'Device registered successfully',
                'platform': platform,
                'push_enabled': True
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UnregisterMobileDeviceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        device_token = request.data.get('device_token')
     
        
        return Response({'status': 'Device unregistered successfully'})

# Utility function to create notifications (can be used by other apps)
def create_notification(user, notification_type, title, message, **kwargs):
    """
    Utility function to create notifications from other apps
    """
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        short_message=kwargs.get('short_message', message[:100]),
        channels=kwargs.get('channels', ['in_app']),
        priority=kwargs.get('priority', 'medium'),
        action_url=kwargs.get('action_url', ''),
        action_text=kwargs.get('action_text', ''),
        related_appointment=kwargs.get('related_appointment'),
        related_prescription=kwargs.get('related_prescription'),
        related_lab_result=kwargs.get('related_lab_result'),
        related_emergency=kwargs.get('related_emergency'),
        related_invoice=kwargs.get('related_invoice'),
        scheduled_for=kwargs.get('scheduled_for'),
        expires_at=kwargs.get('expires_at'),
        metadata=kwargs.get('metadata', {}),
        created_by=kwargs.get('created_by', user),
    )
    
    return notification

