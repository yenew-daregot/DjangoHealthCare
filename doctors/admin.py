from django.contrib import admin
from .models import Specialization, Doctor

@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    search_fields = ['name']

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['doctor_id', 'get_full_name', 'specialization', 'license_number', 'is_available']
    readonly_fields = ['doctor_id']
    list_filter = ['specialization', 'is_available']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'license_number', 'qualification', 'doctor_id']
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = 'Doctor Name'
    get_full_name.admin_order_field = 'user__last_name'

    