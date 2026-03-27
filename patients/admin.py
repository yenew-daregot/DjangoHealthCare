from django.contrib import admin
from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['user', 'blood_group', 'emergency_contact', 'created_at']
    list_filter = ['blood_group', 'created_at']
    search_fields = ['user__username', 'user__email', 'insurance_id']