from django.core.management.base import BaseCommand
from medicationManagment.tasks import medication_scheduler
import time

class Command(BaseCommand):
    help = 'Run the medication reminder scheduler'
    
    def handle(self, *args, **options):
        self.stdout.write('Starting medication scheduler...')
        medication_scheduler.start_background_scheduler()
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stdout.write('Stopping medication scheduler...')
            medication_scheduler.stop_scheduler()