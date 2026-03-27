from django.contrib import admin
from .models import (
    EmergencyContact, EmergencyRequest, EmergencyResponseTeam,
    EmergencyResponse, EmergencyAlert, EmergencyProtocol, EmergencyStatistics
)

class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ['patient', 'name', 'relationship', 'phone_number', 'is_primary', 'can_make_medical_decisions']
    list_filter = ['relationship', 'is_primary', 'can_make_medical_decisions', 'created_at']
    search_fields = ['patient__user__username', 'name', 'phone_number', 'email']
    readonly_fields = ['created_at', 'updated_at']

class EmergencyResponseInline(admin.StackedInline):
    model = EmergencyResponse
    extra = 0
    readonly_fields = ['created_at', 'updated_at']

class EmergencyRequestAdmin(admin.ModelAdmin):
    list_display = [
        'request_id', 'patient', 'emergency_type', 'priority', 'status', 
        'location', 'created_at', 'response_time'
    ]
    list_filter = ['status', 'priority', 'emergency_type', 'created_at']
    search_fields = [
        'request_id', 'patient__user__username', 'location', 'description'
    ]
    readonly_fields = [
        'request_id', 'created_at', 'acknowledged_at', 'dispatched_at',
        'arrived_at', 'transported_at', 'completed_at', 'response_time', 'transport_time'
    ]
    inlines = [EmergencyResponseInline]
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Basic Information', {
            'fields': ('request_id', 'patient', 'emergency_type', 'priority')
        }),
        ('Location', {
            'fields': ('location', 'latitude', 'longitude', 'location_notes')
        }),
        ('Emergency Details', {
            'fields': ('description', 'symptoms', 'medical_notes')
        }),
        ('Vital Signs', {
            'fields': (
                'blood_pressure_systolic', 'blood_pressure_diastolic',
                'heart_rate', 'respiratory_rate', 'oxygen_saturation',
                'temperature', 'gcs_score', 'pain_level'
            ),
            'classes': ('collapse',)
        }),
        ('Patient Status', {
            'fields': ('is_conscious', 'is_breathing', 'has_allergies', 'has_medications')
        }),
        ('Response Information', {
            'fields': ('assigned_doctor', 'first_responder', 'hospital_destination', 'response_notes')
        }),
        ('Status and Timestamps', {
            'fields': (
                'status', 'created_at', 'acknowledged_at', 'dispatched_at',
                'arrived_at', 'transported_at', 'completed_at'
            )
        }),
    )

class EmergencyResponseTeamAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'specialization', 'status', 'is_active', 'phone_number']
    list_filter = ['role', 'status', 'is_active', 'can_prescribe']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'license_number']
    readonly_fields = ['created_at', 'updated_at']

class EmergencyResponseAdmin(admin.ModelAdmin):
    list_display = ['emergency_request', 'team_leader', 'dispatch_time', 'hospital_arrival_time']
    list_filter = ['dispatch_time', 'hospital_arrival_time']
    search_fields = ['emergency_request__request_id', 'team_leader__user__username']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['team_members']

class EmergencyAlertAdmin(admin.ModelAdmin):
    list_display = ['patient', 'alert_type', 'location', 'is_verified', 'created_at']
    list_filter = ['alert_type', 'is_verified', 'is_auto_generated', 'created_at']
    search_fields = ['patient__user__username', 'location', 'message']
    readonly_fields = ['created_at']

class EmergencyProtocolAdmin(admin.ModelAdmin):
    list_display = ['name', 'protocol_type', 'version', 'is_active', 'created_by']
    list_filter = ['protocol_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

class EmergencyStatisticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_emergencies', 'responded_emergencies', 'average_response_time', 'critical_cases']
    list_filter = ['date']
    readonly_fields = ['created_at']

# Register models
admin.site.register(EmergencyContact, EmergencyContactAdmin)
admin.site.register(EmergencyRequest, EmergencyRequestAdmin)
admin.site.register(EmergencyResponseTeam, EmergencyResponseTeamAdmin)
admin.site.register(EmergencyResponse, EmergencyResponseAdmin)
admin.site.register(EmergencyAlert, EmergencyAlertAdmin)
admin.site.register(EmergencyProtocol, EmergencyProtocolAdmin)
admin.site.register(EmergencyStatistics, EmergencyStatisticsAdmin)