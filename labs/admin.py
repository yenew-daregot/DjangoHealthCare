from django.contrib import admin
from .models import LabTest, LabRequest

@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ['name', 'price']
    search_fields = ['name', 'description']
    list_filter = ['price']

@admin.register(LabRequest)
class LabRequestAdmin(admin.ModelAdmin):
    list_display = ['patient', 'test', 'doctor', 'status', 'requested_date', 'completed_date']
    list_filter = ['status', 'requested_date', 'completed_date']
    search_fields = ['patient__user__username', 'test__name', 'doctor__user__username']
    readonly_fields = ['requested_date']
    date_hierarchy = 'requested_date'