
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model

User = get_user_model()

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_doctor_notification_preferences(request, doctor_id):
    """
    GET /api/notifications/doctor-preferences/<doctor_id>/
    
    Get notification preferences for a specific doctor.
    
    Returns:
    {
        "doctor_id": 123,
        "doctor_name": "Dr. John Doe",
        "available_channels": ["sms", "push", "email", "in_app"],
        "preferences": {
            "email_enabled": true,
            "sms_enabled": true,
            "push_enabled": true,
            "in_app_enabled": true,
            "appointment_notifications": true,
            "emergency_notifications": true
        }
    }
    """
    try:
        # Get the doctor
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
    
    # Check permissions
    # Patients can view doctor preferences when booking appointments
    # Doctors can view their own preferences
    # Admins can view anyone's preferences
    user = request.user
    
    if user.role == 'PATIENT' or user.role == 'DOCTOR' or user.role == 'ADMIN':
        # Allow access
        pass
    else:
        return Response(
            {'error': 'Permission denied'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get or create notification preferences
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
            'prescription_notifications': True,
            'lab_result_notifications': True,
            'billing_notifications': True,
            'chat_notifications': True,
            'system_notifications': True,
            'reminder_notifications': True,
            'health_alert_notifications': True,
            'announcement_notifications': True
        }
    )
    
    # Determine available channels based on user data and preferences
    available_channels = []
    
    # Check SMS channel
    if preference.sms_enabled and hasattr(doctor, 'phone_number') and doctor.phone_number:
        available_channels.append('sms')
    
    # Check Push channel
    if preference.push_enabled and hasattr(doctor, 'fcm_token') and doctor.fcm_token:
        available_channels.append('push')
    
    # Check Email channel
    if preference.email_enabled and doctor.email:
        available_channels.append('email')
    
    # Check In-App channel
    if preference.in_app_enabled:
        available_channels.append('in_app')
    
    # Prepare response
    response_data = {
        'doctor_id': doctor.id,
        'doctor_name': doctor.get_full_name() if hasattr(doctor, 'get_full_name') else f"{doctor.first_name} {doctor.last_name}",
        'doctor_email': doctor.email,
        'doctor_phone': getattr(doctor, 'phone_number', None),
        'has_fcm_token': bool(getattr(doctor, 'fcm_token', None)),
        'available_channels': available_channels,
        'preferences': {
            'email_enabled': preference.email_enabled,
            'sms_enabled': preference.sms_enabled,
            'push_enabled': preference.push_enabled,
            'in_app_enabled': preference.in_app_enabled,
            'appointment_notifications': preference.appointment_notifications,
            'emergency_notifications': preference.emergency_notifications,
            'prescription_notifications': preference.prescription_notifications,
            'lab_result_notifications': preference.lab_result_notifications,
            'billing_notifications': preference.billing_notifications,
            'chat_notifications': preference.chat_notifications,
            'system_notifications': preference.system_notifications,
            'reminder_notifications': preference.reminder_notifications,
            'health_alert_notifications': preference.health_alert_notifications,
            'announcement_notifications': preference.announcement_notifications,
            'quiet_hours_start': preference.quiet_hours_start,
            'quiet_hours_end': preference.quiet_hours_end,
            'timezone': preference.timezone,
        }
    }
    
    return Response(response_data)