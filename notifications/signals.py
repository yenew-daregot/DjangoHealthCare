from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from appointments.models import Appointment
from prescriptions.models import Prescription
from labs.models import LabRequest
from billing.models import Invoice
from emergency.models import EmergencyRequest
from .models import Notification, NotificationTemplate
from .views import create_notification

@receiver(post_save, sender=Appointment)
def create_appointment_notification(sender, instance, created, **kwargs):
    if created:
        # Notification for new appointment
        create_notification(
            user=instance.patient.user,
            notification_type='appointment',
            title=f"New Appointment Scheduled",
            message=f"Your appointment with Dr. {instance.doctor.user.get_full_name()} is scheduled for {instance.appointment_date.strftime('%B %d, %Y at %I:%M %p')}",
            short_message=f"New appointment scheduled",
            related_appointment=instance,
            action_url=f"/appointments/{instance.id}",
            action_text="View Appointment"
        )
        
        # Also notify the doctor
        create_notification(
            user=instance.doctor.user,
            notification_type='appointment',
            title=f"New Appointment with {instance.patient.user.get_full_name()}",
            message=f"You have a new appointment with {instance.patient.user.get_full_name()} on {instance.appointment_date.strftime('%B %d, %Y at %I:%M %p')}",
            short_message=f"New appointment scheduled",
            related_appointment=instance,
            action_url=f"/appointments/{instance.id}",
            action_text="View Appointment"
        )

@receiver(post_save, sender=Prescription)
def create_prescription_notification(sender, instance, created, **kwargs):
    if created:
        create_notification(
            user=instance.appointment.patient.user,
            notification_type='prescription',
            title=f"New Prescription from Dr. {instance.appointment.doctor.user.get_full_name()}",
            message=f"Your prescription for {instance.medication.name} is ready. Dosage: {instance.dosage}, Frequency: {instance.frequency}",
            short_message=f"New prescription available",
            related_prescription=instance,
            action_url=f"/prescriptions/{instance.id}",
            action_text="View Prescription"
        )

@receiver(post_save, sender=LabRequest)
def create_lab_result_notification(sender, instance, created, **kwargs):
    if instance.status == 'completed' and instance.result:
        create_notification(
            user=instance.patient.user,
            notification_type='lab_result',
            title=f"Lab Results Ready: {instance.test.name}",
            message=f"Your lab test results for {instance.test.name} are now available.",
            short_message=f"Lab results ready",
            related_lab_result=instance,
            action_url=f"/labs/results/{instance.id}",
            action_text="View Results"
        )

@receiver(post_save, sender=Invoice)
def create_billing_notification(sender, instance, created, **kwargs):
    if created:
        create_notification(
            user=instance.patient.user,
            notification_type='billing',
            title=f"New Invoice #{instance.invoice_number}",
            message=f"A new invoice for ${instance.total_amount} has been issued. Due date: {instance.due_date.strftime('%B %d, %Y')}",
            short_message=f"New invoice available",
            related_invoice=instance,
            action_url=f"/billing/invoices/{instance.id}",
            action_text="View Invoice"
        )

@receiver(post_save, sender=EmergencyRequest)
def create_emergency_notification(sender, instance, created, **kwargs):
    if created:
        # Notify emergency response team (simplified)
        from users.models import CustomUser
        emergency_team = CustomUser.objects.filter(user_type__in=['doctor', 'admin']).first()
        if emergency_team:
            create_notification(
                user=emergency_team,
                notification_type='emergency',
                title=f"Emergency Alert: {instance.patient.user.get_full_name()}",
                message=f"Emergency request from {instance.patient.user.get_full_name()} at {instance.location}. Priority: {instance.priority}",
                short_message=f"Emergency alert",
                priority='critical',
                related_emergency=instance,
                action_url=f"/emergency/requests/{instance.id}",
                action_text="Respond to Emergency"
            )