from django.utils import timezone
from datetime import datetime, timedelta
import threading
import time
from .models import Medication, MedicationSchedule, MedicationDose, MedicationReminder
from .notifications import send_medication_reminder

class MedicationScheduler:
    def __init__(self):
        self.running = False
        self.thread = None
    
    def schedule_medication_reminders(self, medication_id):
        """Schedule reminders for a specific medication"""
        try:
            medication = Medication.objects.get(id=medication_id)
            
            # Clear existing unsent reminders
            MedicationReminder.objects.filter(
                medication=medication, 
                is_sent=False
            ).delete()
            
            # Schedule reminders for the next 7 days
            for day in range(7):
                schedule_date = timezone.now().date() + timedelta(days=day)
                
                for schedule in medication.schedules.filter(is_active=True):
                    # Combine date with scheduled time
                    naive_datetime = datetime.combine(schedule_date, schedule.scheduled_time)
                    reminder_time = timezone.make_aware(naive_datetime)
                    
                    # Create reminder 15 minutes before scheduled time
                    reminder_time = reminder_time - timedelta(minutes=15)
                    
                    if reminder_time > timezone.now():
                        MedicationReminder.objects.create(
                            medication=medication,
                            reminder_time=reminder_time
                        )
            
            print(f"Scheduled reminders for {medication.name}")
            return True
        except Medication.DoesNotExist:
            print("Medication not found")
            return False
        except Exception as e:
            print(f"Error scheduling reminders: {str(e)}")
            return False

    def send_due_reminders(self):
        """Send all due reminders"""
        now = timezone.now()
        due_reminders = MedicationReminder.objects.filter(
            reminder_time__lte=now,
            is_sent=False
        )
        
        sent_count = 0
        for reminder in due_reminders:
            try:
                send_medication_reminder(reminder)
                reminder.is_sent = True
                reminder.sent_at = timezone.now()
                reminder.save()
                sent_count += 1
                print(f"Sent reminder for {reminder.medication.name}")
            except Exception as e:
                print(f"Failed to send reminder {reminder.id}: {e}")
        
        print(f"Sent {sent_count} reminders")
        return sent_count

    def generate_medication_doses(self):
        """Generate dose records for today's medications"""
        today = timezone.now().date()
        created_count = 0
        
        for medication in Medication.objects.filter(is_active=True):
            for schedule in medication.schedules.filter(is_active=True):
                try:
                    # Combine today's date with scheduled time
                    naive_datetime = datetime.combine(today, schedule.scheduled_time)
                    dose_time = timezone.make_aware(naive_datetime)
                    
                    # Create dose record if it doesn't exist
                    dose, created = MedicationDose.objects.get_or_create(
                        medication=medication,
                        scheduled_time=dose_time,
                        defaults={
                            'is_taken': False,
                            'is_skipped': False
                        }
                    )
                    
                    if created:
                        created_count += 1
                except Exception as e:
                    print(f"Error creating dose for {medication.name}: {e}")
        
        print(f"Created {created_count} dose records")
        return created_count

    def start_background_scheduler(self):
        """Start the background scheduler in a separate thread"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
        print("Medication scheduler started")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Check for due reminders every 30 seconds
                self.send_due_reminders()
                
                # Generate doses once per day at 6 AM
                now = timezone.now()
                if now.hour == 6 and now.minute == 0:
                    self.generate_medication_doses()
                
                time.sleep(30)  # Wait 30 seconds
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(60)
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("Medication scheduler stopped")

# Global scheduler instance
medication_scheduler = MedicationScheduler()

# Convenience functions
def schedule_medication_reminders(medication_id):
    return medication_scheduler.schedule_medication_reminders(medication_id)

def send_due_reminders():
    return medication_scheduler.send_due_reminders()

def generate_medication_doses():
    return medication_scheduler.generate_medication_doses()

def start_scheduler():
    return medication_scheduler.start_background_scheduler()

def stop_scheduler():
    return medication_scheduler.stop_scheduler()