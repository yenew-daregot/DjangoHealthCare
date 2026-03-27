from django.core.mail import send_mail
from django.conf import settings

#imports with fallbacks
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("Twilio not installed. SMS notifications disabled.")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Requests not installed. Push notifications disabled.")

def send_medication_reminder(reminder):
    """
    Send medication reminder via multiple channels
    """
    try:
        medication = reminder.medication
        patient = medication.patient
        
        message = f"""
Medication Reminder 💊

It's time to take your medication:

Medication: {medication.name}
Dosage: {medication.dosage} {medication.unit}
Instructions: {medication.instructions or 'No specific instructions'}

Please take your medication now.

Thank you!
        """.strip()
        
        # Track which notifications were sent
        sent_notifications = []
        
        #Email notification
        email_sent = send_email_reminder(patient, medication, message)
        if email_sent:
            sent_notifications.append("Email")
        
        #SMS notification
        sms_sent = send_sms_reminder(patient, message)
        if sms_sent:
            sent_notifications.append("SMS")
        
        #Push notification
        push_sent = send_push_notification(patient, medication, message)
        if push_sent:
            sent_notifications.append("Push")
        
        print(f"📧 Sent reminders via: {', '.join(sent_notifications) if sent_notifications else 'None'}")
        return len(sent_notifications) > 0
        
    except Exception as e:
        print(f"❌ Error sending medication reminder: {e}")
        return False

def send_email_reminder(patient, medication, message):
    """Send email reminder"""
    try:
        if patient.email:
            send_mail(
                subject=f"Medication Reminder: {medication.name}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[patient.email],
                fail_silently=True,
            )
            print(f"📧 Email sent to {patient.email}")
            return True
        else:
            print("⚠️  No email address for patient")
            return False
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False

def send_sms_reminder(patient, message):
    """Send SMS reminder using Twilio"""
    if not TWILIO_AVAILABLE:
        print("⚠️  Twilio not available for SMS")
        return False
        
    try:
        # Check if Twilio is configured in settings
        if (not hasattr(settings, 'TWILIO_ACCOUNT_SID') or 
            not hasattr(settings, 'TWILIO_AUTH_TOKEN') or 
            not hasattr(settings, 'TWILIO_PHONE_NUMBER')):
            print("⚠️  Twilio not configured in settings")
            return False
        # Assuming you have a UserProfile model with phone_number
        phone_number = getattr(patient, 'phone_number', None)
        if not phone_number and hasattr(patient, 'profile'):
            phone_number = getattr(patient.profile, 'phone_number', None)
        
        if not phone_number:
            print("⚠️  No phone number for patient")
            return False
            
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Truncate message for SMS (1600 character limit for Twilio)
        sms_message = message[:1590] + "..." if len(message) > 1590 else message
        
        client.messages.create(
            body=sms_message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        
        print(f"📱 SMS sent to {phone_number}")
        return True
        
    except Exception as e:
        print(f"❌ SMS sending failed: {e}")
        return False

def send_push_notification(patient, medication, message):
    """Send push notification"""
    if not REQUESTS_AVAILABLE:
        print("⚠️  Requests not available for push notifications")
        return False
        
    try:
        # Get FCM token (adjust based on your user model)
        fcm_token = getattr(patient, 'fcm_token', None)
        if not fcm_token and hasattr(patient, 'profile'):
            fcm_token = getattr(patient.profile, 'fcm_token', None)
        
        if not fcm_token:
            print("⚠️  No FCM token for patient")
            return False
        
        # Firebase Cloud Messaging (FCM) implementation
        # You'll need to set FCM_SERVER_KEY in your settings
        if not hasattr(settings, 'FCM_SERVER_KEY'):
            print("⚠️  FCM not configured in settings")
            return False
        
        fcm_data = {
            "to": fcm_token,
            "notification": {
                "title": "Medication Reminder",
                "body": f"Time to take {medication.name}",
                "sound": "default"
            },
            "data": {
                "type": "medication_reminder",
                "medication_id": str(medication.id),
                "medication_name": medication.name,
                "dosage": f"{medication.dosage} {medication.unit}",
                "click_action": "FLUTTER_NOTIFICATION_CLICK"
            }
        }
        
        headers = {
            'Authorization': f'key={settings.FCM_SERVER_KEY}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'https://fcm.googleapis.com/fcm/send',
            json=fcm_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"📱 Push notification sent to {patient.username}")
            return True
        else:
            print(f"❌ FCM error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Push notification failed: {e}")
        return False

# Alternative simple version without external dependencies
def send_simple_reminder(reminder):
    """
    Simple reminder using only email (no external dependencies needed)
    """
    try:
        medication = reminder.medication
        patient = medication.patient
        
        message = f"""
Medication Reminder

It's time to take your medication:

Medication: {medication.name}
Dosage: {medication.dosage} {medication.unit}
Instructions: {medication.instructions or 'No specific instructions'}

Please take your medication now.
        """.strip()
        
        # Only use email (built into Django)
        if patient.email:
            send_mail(
                subject=f"Medication Reminder: {medication.name}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[patient.email],
                fail_silently=False,
            )
            print(f"✅ Email reminder sent to {patient.email}")
            return True
        else:
            print("⚠️  No email address available")
            return False
            
    except Exception as e:
        print(f"❌ Simple reminder failed: {e}")
        return False