from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Prescription, Medication, PrescriptionRefill
from .serializers import (
    PrescriptionSerializer, MedicationSerializer, CreatePrescriptionSerializer,
    UpdatePrescriptionSerializer, PrescriptionRefillSerializer,
    CreatePrescriptionRefillSerializer, PrescriptionSummarySerializer,
    CreateMedicationSerializer
)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def prescription_root(request):
    """Prescription Management System API Root"""
    base_url = request.build_absolute_uri('/api/prescriptions')
    
    endpoints = {
        "api": "Prescription Management System",
        "version": "1.0",
        "description": "Comprehensive prescription and medication management system",
        
        "endpoints": {
            "prescriptions": {
                "list_create": f"{base_url}/",
                "detail": f"{base_url}/{{id}}/",
                "patient_prescriptions": f"{base_url}/patient/{{patient_id}}/",
                "doctor_prescriptions": f"{base_url}/doctor/{{doctor_id}}/",
                "active_prescriptions": f"{base_url}/active/",
                "expired_prescriptions": f"{base_url}/expired/",
            },
            "medications": {
                "list_create": f"{base_url}/medications/",
                "detail": f"{base_url}/medications/{{id}}/",
                "search": f"{base_url}/medications/?search={{query}}",
            },
            "refills": {
                "list_create": f"{base_url}/refills/",
                "detail": f"{base_url}/refills/{{id}}/",
                "approve": f"{base_url}/refills/{{id}}/approve/",
                "deny": f"{base_url}/refills/{{id}}/deny/",
            },
            "dashboard": {
                "doctor_dashboard": f"{base_url}/dashboard/doctor/",
                "patient_dashboard": f"{base_url}/dashboard/patient/",
                "statistics": f"{base_url}/statistics/",
            }
        }
    }
    
    return Response(endpoints)

class PrescriptionListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['medication__name', 'patient__user__first_name', 'patient__user__last_name']
    ordering_fields = ['prescribed_date', 'status', 'medication__name']
    ordering = ['-prescribed_date']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreatePrescriptionSerializer
        return PrescriptionSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Prescription.objects.select_related(
            'appointment', 'patient__user', 'doctor__user', 'medication'
        )
        
        if user.role == 'PATIENT':
            queryset = queryset.filter(patient__user=user)
        elif user.role == 'DOCTOR':
            queryset = queryset.filter(doctor__user=user)
        elif user.role == 'ADMIN':
            pass  # Admin can see all
        else:
            return Prescription.objects.none()
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        medication_filter = self.request.query_params.get('medication')
        if medication_filter:
            queryset = queryset.filter(medication_id=medication_filter)
        
        urgent_filter = self.request.query_params.get('urgent')
        if urgent_filter == 'true':
            queryset = queryset.filter(is_urgent=True)
        
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in ['DOCTOR', 'ADMIN']:
            raise PermissionDenied("Only doctors and admins can create prescriptions.")
        serializer.save()

class PrescriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UpdatePrescriptionSerializer
        return PrescriptionSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Prescription.objects.select_related(
            'appointment', 'patient__user', 'doctor__user', 'medication'
        )
        
        if user.role == 'PATIENT':
            return queryset.filter(patient__user=user)
        elif user.role == 'DOCTOR':
            return queryset.filter(doctor__user=user)
        elif user.role == 'ADMIN':
            return queryset
        else:
            return Prescription.objects.none()

    def perform_update(self, serializer):
        user = self.request.user
        if user.role not in ['DOCTOR', 'ADMIN']:
            raise PermissionDenied("Only doctors and admins can update prescriptions.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if user.role not in ['DOCTOR', 'ADMIN']:
            raise PermissionDenied("Only doctors and admins can delete prescriptions.")
        instance.delete()

class MedicationListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'generic_name', 'manufacturer']
    ordering_fields = ['name', 'medication_type', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateMedicationSerializer
        return MedicationSerializer

    def get_queryset(self):
        queryset = Medication.objects.filter(is_active=True)
        
        # Apply filters
        medication_type = self.request.query_params.get('type')
        if medication_type:
            queryset = queryset.filter(medication_type=medication_type)
        
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in ['DOCTOR', 'ADMIN']:
            raise PermissionDenied("Only doctors and admins can create medications.")
        serializer.save()

class MedicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Medication.objects.all()

    def perform_update(self, serializer):
        user = self.request.user
        if user.role not in ['DOCTOR', 'ADMIN']:
            raise PermissionDenied("Only doctors and admins can update medications.")
        serializer.save()

class PatientPrescriptionsView(generics.ListAPIView):
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        user = self.request.user
        
        if user.role == 'DOCTOR':
            # Verify doctor has appointments with this patient
            from appointments.models import Appointment
            has_appointments = Appointment.objects.filter(
                doctor__user=user, 
                patient_id=patient_id
            ).exists()
            
            if not has_appointments:
                raise PermissionDenied("You can only view prescriptions for your own patients.")
        
        elif user.role == 'PATIENT':
            # Patients can only view their own prescriptions
            if str(user.patient_profile.id) != str(patient_id):
                raise PermissionDenied("You can only view your own prescriptions.")
        
        return Prescription.objects.filter(patient_id=patient_id).select_related(
            'appointment', 'medication', 'doctor__user'
        )

class DoctorPrescriptionsView(generics.ListAPIView):
    serializer_class = PrescriptionSummarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        doctor_id = self.kwargs['doctor_id']
        user = self.request.user
        
        if user.role == 'DOCTOR' and str(user.doctor_profile.id) != str(doctor_id):
            raise PermissionDenied("You can only view your own prescriptions.")
        elif user.role not in ['DOCTOR', 'ADMIN']:
            raise PermissionDenied("Only doctors and admins can access this endpoint.")
        
        return Prescription.objects.filter(doctor_id=doctor_id).select_related(
            'patient__user', 'medication'
        )

class ActivePrescriptionsView(generics.ListAPIView):
    serializer_class = PrescriptionSummarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Prescription.objects.filter(status='active').select_related(
            'patient__user', 'doctor__user', 'medication'
        )
        
        if user.role == 'PATIENT':
            return queryset.filter(patient__user=user)
        elif user.role == 'DOCTOR':
            return queryset.filter(doctor__user=user)
        elif user.role == 'ADMIN':
            return queryset
        else:
            return Prescription.objects.none()

class ExpiredPrescriptionsView(generics.ListAPIView):
    serializer_class = PrescriptionSummarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        today = timezone.now().date()
        queryset = Prescription.objects.filter(
            Q(end_date__lt=today) | Q(status='expired')
        ).select_related('patient__user', 'doctor__user', 'medication')
        
        if user.role == 'PATIENT':
            return queryset.filter(patient__user=user)
        elif user.role == 'DOCTOR':
            return queryset.filter(doctor__user=user)
        elif user.role == 'ADMIN':
            return queryset
        else:
            return Prescription.objects.none()

# Prescription Refill Views
class PrescriptionRefillListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreatePrescriptionRefillSerializer
        return PrescriptionRefillSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = PrescriptionRefill.objects.select_related(
            'prescription__medication', 'prescription__patient__user',
            'requested_by', 'approved_by'
        )
        
        if user.role == 'PATIENT':
            return queryset.filter(requested_by=user)
        elif user.role == 'DOCTOR':
            return queryset.filter(prescription__doctor__user=user)
        elif user.role == 'ADMIN':
            return queryset
        else:
            return PrescriptionRefill.objects.none()

class PrescriptionRefillDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = PrescriptionRefillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = PrescriptionRefill.objects.select_related(
            'prescription__medication', 'prescription__patient__user'
        )
        
        if user.role == 'PATIENT':
            return queryset.filter(requested_by=user)
        elif user.role == 'DOCTOR':
            return queryset.filter(prescription__doctor__user=user)
        elif user.role == 'ADMIN':
            return queryset
        else:
            return PrescriptionRefill.objects.none()

class ApproveRefillView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        if user.role not in ['DOCTOR', 'ADMIN']:
            raise PermissionDenied("Only doctors and admins can approve refills.")
        
        try:
            refill = PrescriptionRefill.objects.get(pk=pk)
            
            # Check if doctor owns the prescription
            if user.role == 'DOCTOR' and refill.prescription.doctor.user != user:
                raise PermissionDenied("You can only approve refills for your own prescriptions.")
            
            if refill.status != 'requested':
                return Response(
                    {'error': 'Refill has already been processed.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update refill status
            refill.status = 'approved'
            refill.approved_by = user
            refill.approved_date = timezone.now()
            refill.save()
            
            # Decrease remaining refills
            prescription = refill.prescription
            prescription.refills_remaining = max(0, prescription.refills_remaining - 1)
            prescription.save()
            
            return Response({
                'message': 'Refill approved successfully.',
                'refill': PrescriptionRefillSerializer(refill).data
            })
            
        except PrescriptionRefill.DoesNotExist:
            return Response(
                {'error': 'Refill not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

class DenyRefillView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        user = request.user
        if user.role not in ['DOCTOR', 'ADMIN']:
            raise PermissionDenied("Only doctors and admins can deny refills.")
        
        try:
            refill = PrescriptionRefill.objects.get(pk=pk)
            
            # Check if doctor owns the prescription
            if user.role == 'DOCTOR' and refill.prescription.doctor.user != user:
                raise PermissionDenied("You can only deny refills for your own prescriptions.")
            
            if refill.status != 'requested':
                return Response(
                    {'error': 'Refill has already been processed.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            denial_reason = request.data.get('denial_reason', '')
            if not denial_reason.strip():
                return Response(
                    {'error': 'Denial reason is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update refill status
            refill.status = 'denied'
            refill.approved_by = user
            refill.approved_date = timezone.now()
            refill.denial_reason = denial_reason
            refill.save()
            
            return Response({
                'message': 'Refill denied.',
                'refill': PrescriptionRefillSerializer(refill).data
            })
            
        except PrescriptionRefill.DoesNotExist:
            return Response(
                {'error': 'Refill not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

# Dashboard Views
class DoctorDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != 'DOCTOR':
            raise PermissionDenied("Only doctors can access this dashboard.")
        
        # Get doctor's prescription statistics
        doctor_prescriptions = Prescription.objects.filter(doctor__user=user)
        
        stats = {
            'total_prescriptions': doctor_prescriptions.count(),
            'active_prescriptions': doctor_prescriptions.filter(status='active').count(),
            'expired_prescriptions': doctor_prescriptions.filter(status='expired').count(),
            'urgent_prescriptions': doctor_prescriptions.filter(is_urgent=True, status='active').count(),
            'pending_refills': PrescriptionRefill.objects.filter(
                prescription__doctor__user=user,
                status='requested'
            ).count(),
        }
        
        # Recent prescriptions
        recent_prescriptions = PrescriptionSummarySerializer(
            doctor_prescriptions.order_by('-prescribed_date')[:10],
            many=True
        ).data
        
        # Pending refills
        pending_refills = PrescriptionRefillSerializer(
            PrescriptionRefill.objects.filter(
                prescription__doctor__user=user,
                status='requested'
            ).order_by('-requested_date')[:5],
            many=True
        ).data
        
        return Response({
            'statistics': stats,
            'recent_prescriptions': recent_prescriptions,
            'pending_refills': pending_refills
        })

class PatientDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != 'PATIENT':
            raise PermissionDenied("Only patients can access this dashboard.")
        
        # Get patient's prescription statistics
        patient_prescriptions = Prescription.objects.filter(patient__user=user)
        
        stats = {
            'total_prescriptions': patient_prescriptions.count(),
            'active_prescriptions': patient_prescriptions.filter(status='active').count(),
            'expired_prescriptions': patient_prescriptions.filter(status='expired').count(),
            'expiring_soon': patient_prescriptions.filter(
                status='active',
                end_date__lte=timezone.now().date() + timedelta(days=7)
            ).count(),
            'pending_refills': PrescriptionRefill.objects.filter(
                requested_by=user,
                status='requested'
            ).count(),
        }
        
        # Active prescriptions
        active_prescriptions = PrescriptionSummarySerializer(
            patient_prescriptions.filter(status='active').order_by('-prescribed_date'),
            many=True
        ).data
        
        # Recent refill requests
        recent_refills = PrescriptionRefillSerializer(
            PrescriptionRefill.objects.filter(requested_by=user).order_by('-requested_date')[:5],
            many=True
        ).data
        
        return Response({
            'statistics': stats,
            'active_prescriptions': active_prescriptions,
            'recent_refills': recent_refills
        })

class PrescriptionStatisticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != 'ADMIN':
            raise PermissionDenied("Only admins can access prescription statistics.")
        
        # Overall statistics
        total_prescriptions = Prescription.objects.count()
        active_prescriptions = Prescription.objects.filter(status='active').count()
        
        # Most prescribed medications
        top_medications = Medication.objects.annotate(
            prescription_count=Count('prescriptions')
        ).order_by('-prescription_count')[:10]
        
        # Recent activity
        recent_prescriptions = Prescription.objects.order_by('-prescribed_date')[:20]
        
        return Response({
            'total_prescriptions': total_prescriptions,
            'active_prescriptions': active_prescriptions,
            'top_medications': MedicationSerializer(top_medications, many=True).data,
            'recent_prescriptions': PrescriptionSummarySerializer(recent_prescriptions, many=True).data
        })