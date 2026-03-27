from django.contrib import admin
from .models import (
    MedicalRecord, Allergy, Diagnosis, MedicationHistory,
    SurgicalHistory, FamilyHistory, ImmunizationRecord, VitalSignsRecord
)

class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = [
        'patient', 'record_type', 'title', 'doctor', 'date_recorded', 
        'priority', 'requires_follow_up'
    ]
    list_filter = [
        'record_type', 'priority', 'requires_follow_up', 'date_recorded', 
        'created_at'
    ]
    search_fields = [
        'patient__user__username', 'patient__user__first_name', 
        'patient__user__last_name', 'title', 'description', 'diagnosis_codes'
    ]
    readonly_fields = ['created_at', 'updated_at', 'file_size', 'bmi']
    date_hierarchy = 'date_recorded'
    fieldsets = (
        ('Basic Information', {
            'fields': ('patient', 'doctor', 'record_type', 'title', 'description')
        }),
        ('Clinical Information', {
            'fields': ('clinical_notes', 'diagnosis_codes', 'procedure_codes', 
                      'symptoms', 'medications', 'allergies')
        }),
        ('Vital Signs', {
            'fields': ('blood_pressure_systolic', 'blood_pressure_diastolic', 
                      'heart_rate', 'temperature', 'respiratory_rate', 
                      'oxygen_saturation', 'height', 'weight', 'bmi'),
            'classes': ('collapse',)
        }),
        ('Dates and Status', {
            'fields': ('date_recorded', 'date_effective', 'priority', 
                      'is_confidential', 'requires_follow_up', 'follow_up_date')
        }),
        ('Related Records', {
            'fields': ('appointment', 'lab_request', 'prescription'),
            'classes': ('collapse',)
        }),
        ('Files', {
            'fields': ('file', 'file_name', 'file_size'),
            'classes': ('collapse',)
        }),
        ('Audit Trail', {
            'fields': ('created_by', 'last_modified_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

class AllergyAdmin(admin.ModelAdmin):
    list_display = ['patient', 'allergen', 'allergen_type', 'severity', 'reaction', 'is_active']
    list_filter = ['allergen_type', 'severity', 'is_active', 'created_at']
    search_fields = ['patient__user__username', 'allergen', 'symptoms']
    readonly_fields = ['created_at', 'updated_at']

class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ['patient', 'diagnosis_code', 'description', 'status', 'date_diagnosed', 'is_primary']
    list_filter = ['status', 'is_primary', 'date_diagnosed']
    search_fields = ['patient__user__username', 'diagnosis_code', 'description']
    readonly_fields = ['created_at']

class MedicationHistoryAdmin(admin.ModelAdmin):
    list_display = ['patient', 'medication_name', 'dosage', 'status', 'start_date', 'prescribed_by']
    list_filter = ['status', 'route', 'start_date']
    search_fields = ['patient__user__username', 'medication_name', 'reason']
    readonly_fields = ['created_at']

class SurgicalHistoryAdmin(admin.ModelAdmin):
    list_display = ['patient', 'procedure_name', 'procedure_date', 'surgeon']
    list_filter = ['procedure_date']
    search_fields = ['patient__user__username', 'procedure_name', 'surgeon']
    readonly_fields = ['created_at']

class FamilyHistoryAdmin(admin.ModelAdmin):
    list_display = ['patient', 'relation', 'condition', 'age_at_diagnosis']
    list_filter = ['relation']
    search_fields = ['patient__user__username', 'relation', 'condition']
    readonly_fields = ['created_at']

class ImmunizationRecordAdmin(admin.ModelAdmin):
    list_display = ['patient', 'vaccine_name', 'administration_date', 'next_due_date']
    list_filter = ['vaccine_name', 'administration_date']
    search_fields = ['patient__user__username', 'vaccine_name']
    readonly_fields = ['created_at']

class VitalSignsRecordAdmin(admin.ModelAdmin):
    list_display = ['patient', 'recorded_by', 'recorded_date', 'blood_pressure', 'heart_rate', 'temperature']
    list_filter = ['recorded_date']
    search_fields = ['patient__user__username', 'recorded_by__user__username']
    readonly_fields = ['created_at', 'bmi']

# Register models
admin.site.register(MedicalRecord, MedicalRecordAdmin)
admin.site.register(Allergy, AllergyAdmin)
admin.site.register(Diagnosis, DiagnosisAdmin)
admin.site.register(MedicationHistory, MedicationHistoryAdmin)
admin.site.register(SurgicalHistory, SurgicalHistoryAdmin)
admin.site.register(FamilyHistory, FamilyHistoryAdmin)
admin.site.register(ImmunizationRecord, ImmunizationRecordAdmin)
admin.site.register(VitalSignsRecord, VitalSignsRecordAdmin)