from django.contrib import admin
from .models import*

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'patient', 'dosage', 'frequency', 'is_active']
    list_filter = ['frequency', 'is_active']
    search_fields = ['name', 'patient__username']

@admin.register(MedicationSchedule)
class MedicationScheduleAdmin(admin.ModelAdmin):
    list_display = ['medication', 'scheduled_time', 'is_active']

@admin.register(MedicationDose)
class MedicationDoseAdmin(admin.ModelAdmin):
    list_display = ['medication', 'scheduled_time', 'is_taken', 'is_skipped']
    list_filter = ['is_taken', 'is_skipped', 'scheduled_time']

@admin.register(MedicationReminder)
class MedicationReminderAdmin(admin.ModelAdmin):
    list_display = ['medication', 'reminder_time', 'is_sent']
    list_filter = ['is_sent', 'reminder_time']