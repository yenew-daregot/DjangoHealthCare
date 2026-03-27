from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'appointment_date', 'status', 'duration']
    list_filter = ['status', 'appointment_date', 'created_at']
    search_fields = ['patient__user__username', 'doctor__user__username', 'reason']
    date_hierarchy = 'appointment_date'