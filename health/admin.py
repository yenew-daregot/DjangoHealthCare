from django.contrib import admin
from .models import VitalType, VitalReading, HealthAlert, PatientHealthSummary, HealthReport

@admin.register(VitalType)
class VitalTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'unit', 'normal_min', 'normal_max', 'is_active']
    list_filter = ['is_active', 'name']
    search_fields = ['name', 'display_name']

@admin.register(VitalReading)
class VitalReadingAdmin(admin.ModelAdmin):
    list_display = ['patient', 'vital_type', 'value', 'unit', 'recorded_at', 'is_abnormal', 'doctor']
    list_filter = ['vital_type', 'is_abnormal', 'is_manual', 'recorded_at']
    search_fields = ['patient__user__first_name', 'patient__user__last_name', 'notes']
    date_hierarchy = 'recorded_at'
    readonly_fields = ['is_abnormal', 'created_at', 'updated_at']

@admin.register(HealthAlert)
class HealthAlertAdmin(admin.ModelAdmin):
    list_display = ['patient', 'title', 'severity', 'is_resolved', 'created_at']
    list_filter = ['severity', 'is_resolved', 'created_at']
    search_fields = ['patient__user__first_name', 'patient__user__last_name', 'title', 'message']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['mark_resolved']
    
    def mark_resolved(self, request, queryset):
        for alert in queryset:
            alert.resolve(user=request.user)
        self.message_user(request, f'{queryset.count()} alerts marked as resolved.')
    mark_resolved.short_description = 'Mark selected alerts as resolved'

@admin.register(PatientHealthSummary)
class PatientHealthSummaryAdmin(admin.ModelAdmin):
    list_display = ['patient', 'risk_level', 'total_readings', 'abnormal_readings', 'active_alerts', 'last_updated']
    list_filter = ['risk_level', 'last_updated']
    search_fields = ['patient__user__first_name', 'patient__user__last_name']
    readonly_fields = ['total_readings', 'abnormal_readings', 'active_alerts', 'last_updated', 'created_at']
    
    actions = ['update_summaries']
    
    def update_summaries(self, request, queryset):
        for summary in queryset:
            summary.update_summary()
        self.message_user(request, f'{queryset.count()} summaries updated.')
    update_summaries.short_description = 'Update selected health summaries'

@admin.register(HealthReport)
class HealthReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'report_type', 'patient', 'generated_by', 'is_shared_with_admin', 'created_at']
    list_filter = ['report_type', 'is_shared_with_admin', 'created_at']
    search_fields = ['title', 'patient__user__first_name', 'patient__user__last_name']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']