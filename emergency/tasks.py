from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings 
from django.utils.html import strip_tags
import requests
import os

@shared_task
def notify_emergency_contacts_async(patient_id, emergency_request_id):
    from .models import Patient, EmergencyRequest, EmergencyContact
    from django.utils import timezone
    
    try:
        patient = Patient.objects.get(id=patient_id)
        emergency_request = EmergencyRequest.objects.get(id=emergency_request_id)
        contacts = EmergencyContact.objects.filter(patient=patient)
        
        for contact in contacts:
            # Send notifications asynchronously
            send_contact_email.delay(contact.id, emergency_request_id)
            send_contact_sms.delay(contact.id, emergency_request_id)
            
    except Exception as e:
        print(f"Async notification failed for patient {patient_id}: {str(e)}")

@shared_task
def send_contact_email(contact_id, emergency_request_id):
    from .models import EmergencyContact, EmergencyRequest
    
    try:
        contact = EmergencyContact.objects.get(id=contact_id)
        emergency_request = EmergencyRequest.objects.get(id=emergency_request_id)
        
        subject = f"EMERGENCY ALERT: {emergency_request.patient.user.get_full_name()} Needs Help"
        
        context = {
            'contact_name': contact.name,
            'patient_name': emergency_request.patient.user.get_full_name(),
            'emergency_type': emergency_request.get_emergency_type_display(),
            'location': emergency_request.location,
            'description': emergency_request.description,
            'time': emergency_request.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        html_message = render_to_string('emails/emergency_alert.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[contact.email],
            html_message=html_message,
            fail_silently=True,
        )
        
    except Exception as e:
        print(f"Email sending failed for contact {contact_id}: {str(e)}")

@shared_task
def send_contact_sms(contact_id, emergency_request_id):
    """Send SMS using environment variables"""
    from .models import EmergencyContact, EmergencyRequest
    
    try:
        contact = EmergencyContact.objects.get(id=contact_id)
        emergency_request = EmergencyRequest.objects.get(id=emergency_request_id)
        
        # Get Twilio credentials from environment variables
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        twilio_phone = os.environ.get('TWILIO_PHONE_NUMBER')
        
        # Check if Twilio is configured
        if not all([account_sid, auth_token, twilio_phone]):
            print("Twilio not configured - skipping SMS")
            return
        
        from twilio.rest import Client
        
        client = Client(account_sid, auth_token)
        
        message = (
            f"EMERGENCY: {emergency_request.patient.user.get_full_name()} needs help. "
            f"Location: {emergency_request.location}. "
            f"Emergency: {emergency_request.get_emergency_type_display()}. "
            f"Time: {emergency_request.created_at.strftime('%H:%M')}. "
            f"Please respond immediately."
        )
        
        # Send SMS
        client.messages.create(
            body=message,
            from_=twilio_phone,
            to=contact.phone_number
        )
        
    except ImportError:
        print("Twilio not installed. Run: pip install twilio")
    except Exception as e:
        print(f"SMS sending failed for {contact_id}: {str(e)}")