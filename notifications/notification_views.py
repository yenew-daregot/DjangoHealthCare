"""
Notification API Views
Handles notification sending, preferences, and history
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import Notification, NotificationPreference
from .notification_serializers import NotificationSerializer, NotificationPreferenceSerializer
from .notification_service import get_notification_service  

class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing notifications"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def send(self, request):
        """Send a notification through multiple channels"""
        title = request.data.get('title')
        message = request.data.get('message')
        notification_type = request.data.get('notification_type', 'info')
        channels = request.data.get('channels', ['in_app'])
        data = request.data.get('data', {})
        
        if not title or not message:
            return Response(
                {'error': 'Title and message are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            notification_service = get_notification_service()
            results = notification_service.send_notification(
                user=request.user,
                title=title,
                message=message,
                notification_type=notification_type,
                channels=channels,
                data=data
            )
            
            return Response({
                'success': True,
                'results': results,
                'message': 'Notification sent successfully'
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get notification history with pagination"""
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get notifications
        notifications = self.get_queryset()[offset:offset + limit]
        total = self.get_queryset().count()
        
        serializer = self.get_serializer(notifications, many=True)
        
        return Response({
            'notifications': serializer.data,
            'total': total,
            'page': page,
            'limit': limit,
            'has_next': offset + limit < total
        })
    
    @action(detail=True, methods=['patch'])
    def read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        updated_count = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'success': True,
            'updated_count': updated_count,
            'message': f'{updated_count} notifications marked as read'
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['delete'])
    def clear_old(self, request):
        """Clear notifications older than 30 days"""
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count, _ = self.get_queryset().filter(
            created_at__lt=cutoff_date
        ).delete()
        
        return Response({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'{deleted_count} old notifications cleared'
        })

class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing notification preferences"""
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Get or create notification preferences for the user"""
        preference, created = NotificationPreference.objects.get_or_create(
            user=self.request.user,
            defaults={
                'sms_enabled': True,
                'push_enabled': True,
                'email_enabled': True,
                'in_app_enabled': True,
                'appointment_notifications': True,
                'health_alert_notifications': True,
                'emergency_notifications': True,
                'prescription_notifications': True,
                'lab_result_notifications': True,
                'billing_notifications': True,
                'chat_notifications': True,
                'system_notifications': True,
                'reminder_notifications': True,
                'announcement_notifications': False
            }
        )
        return preference
    
    @action(detail=False, methods=['get'])
    def preferences(self, request):
        """Get user notification preferences"""
        preference = self.get_object()
        serializer = self.get_serializer(preference)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'])
    def update_preferences(self, request):
        """Update user notification preferences"""
        preference = self.get_object()
        serializer = self.get_serializer(preference, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'preferences': serializer.data,
                'message': 'Preferences updated successfully'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def update_fcm_token(self, request):
        """Update FCM token for push notifications"""
        fcm_token = request.data.get('fcm_token')
        
        if not fcm_token:
            return Response(
                {'error': 'FCM token is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update user's FCM token 
        user = request.user
        user.fcm_token = fcm_token
        user.save()
        
        return Response({
            'success': True,
            'message': 'FCM token updated successfully'
        })
    
    @action(detail=False, methods=['get'])
    def service_status(self, request):
        """Get status of notification services"""
        notification_service = get_notification_service()
        status_info = notification_service.get_service_status()
        return Response(status_info)

# Additional utility views
from rest_framework.decorators import api_view, permission_classes

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def test_notification(request):
    """Test notification endpoint for development"""
    notification_type = request.data.get('type', 'info')
    channels = request.data.get('channels', ['in_app'])
    
    test_messages = {
        'info': 'This is a test info notification',
        'success': 'This is a test success notification',
        'warning': 'This is a test warning notification',
        'error': 'This is a test error notification',
        'urgent': 'This is a test urgent notification',
        'emergency': 'This is a test emergency notification'
    }
    
    message = test_messages.get(notification_type, 'Test notification')
    
    try:
        notification_service = get_notification_service()
        results = notification_service.send_notification(
            user=request.user,
            title='Test Notification',
            message=message,
            notification_type=notification_type,
            channels=channels,
            data={'test': True}
        )
        
        return Response({
            'success': True,
            'results': results,
            'message': 'Test notification sent successfully'
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def test_doctor_notification(request):
    """Test sending notification to doctor"""
    doctor_id = request.data.get('doctor_id')
    
    if not doctor_id:
        return Response(
            {'error': 'doctor_id is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        doctor = User.objects.get(id=doctor_id, role='DOCTOR')
        
        notification_service = get_notification_service()
        
        # Send test notification
        results = notification_service.send_notification(
            user=doctor,
            title='Test Notification',
            message='This is a test notification from the healthcare system.',
            notification_type='info',
            channels=['sms', 'push', 'email', 'in_app'],
            data={'test': True, 'source': 'test_endpoint'}
        )
        
        return Response({
            'success': True,
            'doctor': f"Dr. {doctor.first_name} {doctor.last_name}",
            'channels_used': list(results.keys()),
            'results': results
        })
        
    except User.DoesNotExist:
        return Response(
            {'error': 'Doctor not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_health_alert(request):
    """Send health alert notification"""
    vital_reading_id = request.data.get('vital_reading_id')
    
    if not vital_reading_id:
        return Response(
            {'error': 'vital_reading_id is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from health.models import VitalReading
        vital_reading = VitalReading.objects.get(id=vital_reading_id)
        
        notification_service = get_notification_service()
        notification_service.notify_health_alert(vital_reading)
        
        return Response({
            'success': True,
            'message': 'Health alert notification sent successfully'
        })
        
    except VitalReading.DoesNotExist:
        return Response(
            {'error': 'Vital reading not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )