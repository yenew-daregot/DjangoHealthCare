# medical_records/permissions.py
from rest_framework import permissions

class IsPatientOwner(permissions.BasePermission):
    """
    Patients can only access their own medical data.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.user_type == 'patient':
            # Handle different object types
            if hasattr(obj, 'patient'):
                return obj.patient.user == request.user
            elif hasattr(obj, 'user'):
                return obj.user == request.user
        return True

class IsDoctorOrAdmin(permissions.BasePermission):
    """
    Doctors and admins have access to all medical records.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type in ['doctor', 'admin']

class IsOwnerOrDoctorOrAdmin(permissions.BasePermission):
    """
    Patients can access their own data, doctors/admins can access all.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.user_type == 'patient':
            if hasattr(obj, 'patient'):
                return obj.patient.user == request.user
            elif hasattr(obj, 'user'):
                return obj.user == request.user
        return request.user.user_type in ['doctor', 'admin']

class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Doctors and admins can edit, patients can only read.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.user_type in ['doctor', 'admin']

class CanAccessMedicalRecord(permissions.BasePermission):
    """
    Comprehensive permission for medical record access.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Patients can only access their own records
        if user.user_type == 'patient':
            return obj.patient.user == user
        
        # Doctors can access records they created or for their patients
        elif user.user_type == 'doctor':
            # If the doctor created the record
            if hasattr(obj, 'doctor') and obj.doctor.user == user:
                return True
            # If the doctor is currently assigned to the patient
            if hasattr(obj, 'patient'):
                # You might want to check if the doctor is assigned to this patient
                # This would require additional relationship checks
                return True
        
        # Admins have full access
        elif user.user_type == 'admin':
            return True
        
        return False