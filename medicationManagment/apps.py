from django.apps import AppConfig

class medicationManagmentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'medicationManagment'
    
    def ready(self):
        # Start the medication scheduler when Django starts
        import os
        if os.environ.get('RUN_MAIN'):
            from .tasks import start_scheduler
            start_scheduler()