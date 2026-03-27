from django.contrib import admin
from .models import Medication, Prescription

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'generic_name', 'manufacturer']
    search_fields = ['name', 'generic_name']

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'medication', 'dosage', 'frequency', 'prescribed_date']
    list_filter = ['prescribed_date']
    search_fields = ['appointment__patient__user__username', 'medication__name']