from rest_framework import generics, permissions, status, filters, viewsets  # Added viewsets here
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q, Count, Max, Min
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from .models import (
    MedicalRecord, Allergy, Diagnosis, MedicationHistory,
    SurgicalHistory, FamilyHistory, ImmunizationRecord, VitalSignsRecord
)
from .serializers import (
    MedicalRecordSerializer, MedicalRecordDetailSerializer,
    AllergySerializer, DiagnosisSerializer, MedicationHistorySerializer,
    SurgicalHistorySerializer, FamilyHistorySerializer,
    ImmunizationRecordSerializer, VitalSignsRecordSerializer,
    MedicalRecordFileUploadSerializer, PatientMedicalSummarySerializer,
    PatientTimelineSerializer
)
from patients.models import Patient
from doctors.models import Doctor
from django_filters.rest_framework import DjangoFilterBackend

# Medical Records Views
class MedicalRecordListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['record_type', 'priority', 'date_recorded']
    search_fields = ['title', 'description', 'clinical_notes']
    ordering_fields = ['date_recorded', 'created_at', 'priority']
    ordering = ['-date_recorded']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return MedicalRecord.objects.filter(patient__user=user)
        elif user.role == 'doctor':
            return MedicalRecord.objects.filter(doctor__user=user)
        elif user.role == 'admin':
            return MedicalRecord.objects.all()
        else:
            return MedicalRecord.objects.none()

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            last_modified_by=self.request.user
        )

class MedicalRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicalRecordDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return MedicalRecord.objects.filter(patient__user=user)
        elif user.role == 'doctor':
            return MedicalRecord.objects.filter(doctor__user=user)
        elif user.role == 'admin':
            return MedicalRecord.objects.all()
        else:
            return MedicalRecord.objects.none()

    def perform_update(self, serializer):
        serializer.save(last_modified_by=self.request.user)

class PatientMedicalRecordsView(generics.ListAPIView):
    serializer_class = MedicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['record_type', 'priority']
    search_fields = ['title', 'description']
    ordering_fields = ['date_recorded', 'created_at']
    ordering = ['-date_recorded']

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        return MedicalRecord.objects.filter(patient_id=patient_id)

class DoctorMedicalRecordsView(generics.ListAPIView):
    serializer_class = MedicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['record_type', 'priority']
    search_fields = ['title', 'description']
    ordering_fields = ['date_recorded', 'created_at']
    ordering = ['-date_recorded']

    def get_queryset(self):
        doctor_id = self.kwargs['doctor_id']
        return MedicalRecord.objects.filter(doctor_id=doctor_id)

class MedicalRecordsByTypeView(generics.ListAPIView):
    serializer_class = MedicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['date_recorded', 'created_at']
    ordering = ['-date_recorded']

    def get_queryset(self):
        record_type = self.kwargs['record_type']
        user = self.request.user
        
        if user.role == 'patient':
            return MedicalRecord.objects.filter(
                patient__user=user,
                record_type=record_type
            )
        elif user.role == 'doctor':
            return MedicalRecord.objects.filter(
                doctor__user=user,
                record_type=record_type
            )
        else:
            return MedicalRecord.objects.filter(record_type=record_type)

# Allergy Views
class AllergyListCreateView(generics.ListCreateAPIView):
    serializer_class = AllergySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['allergen_type', 'severity', 'is_active']
    search_fields = ['allergen', 'symptoms', 'notes']
    ordering_fields = ['severity', 'onset_date']
    ordering = ['-severity']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return Allergy.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return Allergy.objects.all()
        else:
            return Allergy.objects.none()

class AllergyDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AllergySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return Allergy.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return Allergy.objects.all()
        else:
            return Allergy.objects.none()

class PatientAllergiesView(generics.ListAPIView):
    serializer_class = AllergySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['allergen_type', 'severity']
    ordering_fields = ['severity', 'onset_date']
    ordering = ['-severity']

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        return Allergy.objects.filter(patient_id=patient_id, is_active=True)

# Diagnosis Views
class DiagnosisListCreateView(generics.ListCreateAPIView):
    serializer_class = DiagnosisSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_primary']
    search_fields = ['diagnosis_code', 'description', 'notes']
    ordering_fields = ['date_diagnosed', 'status']
    ordering = ['-date_diagnosed']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return Diagnosis.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return Diagnosis.objects.all()
        else:
            return Diagnosis.objects.none()

class DiagnosisDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DiagnosisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return Diagnosis.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return Diagnosis.objects.all()
        else:
            return Diagnosis.objects.none()

class PatientDiagnosesView(generics.ListAPIView):
    serializer_class = DiagnosisSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'is_primary']
    ordering_fields = ['date_diagnosed']
    ordering = ['-date_diagnosed']

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        return Diagnosis.objects.filter(patient_id=patient_id)

# Medication History Views
class MedicationHistoryListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicationHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'route']
    search_fields = ['medication_name', 'dosage', 'reason']
    ordering_fields = ['start_date', 'status']
    ordering = ['-start_date']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return MedicationHistory.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return MedicationHistory.objects.all()
        else:
            return MedicationHistory.objects.none()

class MedicationHistoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicationHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return MedicationHistory.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return MedicationHistory.objects.all()
        else:
            return MedicationHistory.objects.none()

class PatientMedicationsView(generics.ListAPIView):
    serializer_class = MedicationHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'route']
    ordering_fields = ['start_date']
    ordering = ['-start_date']

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        return MedicationHistory.objects.filter(patient_id=patient_id)

# Surgical History Views
class SurgicalHistoryListCreateView(generics.ListCreateAPIView):
    serializer_class = SurgicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['procedure_name', 'surgeon', 'hospital']
    ordering_fields = ['procedure_date']
    ordering = ['-procedure_date']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return SurgicalHistory.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return SurgicalHistory.objects.all()
        else:
            return SurgicalHistory.objects.none()

class SurgicalHistoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SurgicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return SurgicalHistory.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return SurgicalHistory.objects.all()
        else:
            return SurgicalHistory.objects.none()

class PatientSurgicalHistoryView(generics.ListAPIView):
    serializer_class = SurgicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['procedure_date']
    ordering = ['-procedure_date']

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        return SurgicalHistory.objects.filter(patient_id=patient_id)

# Family History Views
class FamilyHistoryListCreateView(generics.ListCreateAPIView):
    serializer_class = FamilyHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['relation', 'condition']
    ordering_fields = ['relation']
    ordering = ['relation']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return FamilyHistory.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return FamilyHistory.objects.all()
        else:
            return FamilyHistory.objects.none()

class FamilyHistoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FamilyHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return FamilyHistory.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return FamilyHistory.objects.all()
        else:
            return FamilyHistory.objects.none()

class PatientFamilyHistoryView(generics.ListAPIView):
    serializer_class = FamilyHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['relation']
    ordering = ['relation']

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        return FamilyHistory.objects.filter(patient_id=patient_id)

# Immunization Views
class ImmunizationListCreateView(generics.ListCreateAPIView):
    serializer_class = ImmunizationRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['vaccine_name', 'manufacturer']
    ordering_fields = ['administration_date', 'next_due_date']
    ordering = ['-administration_date']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return ImmunizationRecord.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return ImmunizationRecord.objects.all()
        else:
            return ImmunizationRecord.objects.none()

class ImmunizationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ImmunizationRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return ImmunizationRecord.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return ImmunizationRecord.objects.all()
        else:
            return ImmunizationRecord.objects.none()

class PatientImmunizationsView(generics.ListAPIView):
    serializer_class = ImmunizationRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['administration_date']
    ordering = ['-administration_date']

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        return ImmunizationRecord.objects.filter(patient_id=patient_id)

# Vital Signs Views
class VitalSignsListCreateView(generics.ListCreateAPIView):
    serializer_class = VitalSignsRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['recorded_date']
    ordering = ['-recorded_date']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return VitalSignsRecord.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return VitalSignsRecord.objects.all()
        else:
            return VitalSignsRecord.objects.none()

class VitalSignsDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VitalSignsRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return VitalSignsRecord.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return VitalSignsRecord.objects.all()
        else:
            return VitalSignsRecord.objects.none()

class PatientVitalSignsView(generics.ListAPIView):
    serializer_class = VitalSignsRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['recorded_date']
    ordering = ['-recorded_date']

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        return VitalSignsRecord.objects.filter(patient_id=patient_id)

# File Upload View
class MedicalRecordFileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MedicalRecordFileUploadSerializer(data=request.data)
        if serializer.is_valid():
            # In a real implementation, you would create a medical record with the file
            # For now, return the file information
            file = serializer.validated_data['file']
            return Response({
                'file_name': file.name,
                'file_size': file.size,
                'content_type': file.content_type,
                'message': 'File uploaded successfully. Medical record would be created with this file.'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Reports and Summaries
class PatientMedicalSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, patient_id):
        try:
            patient = Patient.objects.get(id=patient_id)
            
            # Verify access permissions
            user = request.user
            if user.role == 'patient' and patient.user != user:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Gather comprehensive medical summary
            summary_data = self.generate_medical_summary(patient)
            serializer = PatientMedicalSummarySerializer(summary_data)
            return Response(serializer.data)
            
        except Patient.DoesNotExist:
            return Response(
                {'error': 'Patient not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def generate_medical_summary(self, patient):
        # Recent medical records (last 30 days)
        recent_records = MedicalRecord.objects.filter(
            patient=patient,
            date_recorded__gte=timezone.now() - timedelta(days=30)
        )[:10]
        
        # Active conditions
        active_diagnoses = Diagnosis.objects.filter(
            patient=patient,
            status__in=['active', 'chronic']
        )
        
        # Current medications
        current_medications = MedicationHistory.objects.filter(
            patient=patient,
            status='active'
        )
        
        # Active allergies
        active_allergies = Allergy.objects.filter(
            patient=patient,
            is_active=True
        )
        
        # Recent vital signs
        recent_vitals = VitalSignsRecord.objects.filter(
            patient=patient
        ).order_by('-recorded_date')[:5]
        
        # Upcoming immunizations
        upcoming_immunizations = ImmunizationRecord.objects.filter(
            patient=patient,
            next_due_date__gte=timezone.now().date()
        ).order_by('next_due_date')
        
        # Statistics
        total_records = MedicalRecord.objects.filter(patient=patient).count()
        record_types = MedicalRecord.objects.filter(patient=patient).values(
            'record_type'
        ).annotate(count=Count('id'))
        
        return {
            'patient': patient,
            'recent_records': recent_records,
            'active_diagnoses': active_diagnoses,
            'current_medications': current_medications,
            'active_allergies': active_allergies,
            'recent_vitals': recent_vitals,
            'upcoming_immunizations': upcoming_immunizations,
            'statistics': {
                'total_records': total_records,
                'record_types': list(record_types),
                'last_updated': timezone.now()
            }
        }

class PatientMedicalTimelineView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, patient_id):
        try:
            patient = Patient.objects.get(id=patient_id)
            
            # Verify access permissions
            user = request.user
            if user.role == 'patient' and patient.user != user:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get timeline data
            timeline_data = self.generate_timeline(patient)
            serializer = PatientTimelineSerializer(timeline_data, many=True)
            return Response(serializer.data)
            
        except Patient.DoesNotExist:
            return Response(
                {'error': 'Patient not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def generate_timeline(self, patient):
        timeline = []
        
        # Add medical records to timeline
        medical_records = MedicalRecord.objects.filter(
            patient=patient
        ).select_related('doctor').order_by('-date_recorded')[:50]
        
        for record in medical_records:
            timeline.append({
                'type': 'medical_record',
                'date': record.date_recorded,
                'title': record.title,
                'description': f"{record.record_type} by Dr. {record.doctor.user.get_full_name()}",
                'data': MedicalRecordSerializer(record).data
            })
        
        # Add diagnoses to timeline
        diagnoses = Diagnosis.objects.filter(
            patient=patient
        ).select_related('doctor').order_by('-date_diagnosed')[:20]
        
        for diagnosis in diagnoses:
            timeline.append({
                'type': 'diagnosis',
                'date': diagnosis.date_diagnosed,
                'title': f"Diagnosis: {diagnosis.description}",
                'description': f"Diagnosed by Dr. {diagnosis.doctor.user.get_full_name()}",
                'data': DiagnosisSerializer(diagnosis).data
            })
        
        # Add medications to timeline
        medications = MedicationHistory.objects.filter(
            patient=patient
        ).select_related('prescribed_by').order_by('-start_date')[:20]
        
        for medication in medications:
            timeline.append({
                'type': 'medication',
                'date': medication.start_date,
                'title': f"Medication: {medication.medication_name}",
                'description': f"Prescribed by Dr. {medication.prescribed_by.user.get_full_name()}",
                'data': MedicationHistorySerializer(medication).data
            })
        
        # Sort timeline by date
        timeline.sort(key=lambda x: x['date'], reverse=True)
        return timeline[:100]  # Limit to 100 most recent items

class HealthOverviewReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Only doctors and admins can access health overview reports
        if request.user.role not in ['doctor', 'admin']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate health overview statistics
        report_data = {
            'total_patients': Patient.objects.count(),
            'total_records': MedicalRecord.objects.count(),
            'record_types': MedicalRecord.objects.values('record_type').annotate(
                count=Count('id')
            ),
            'recent_activity': MedicalRecord.objects.filter(
                date_recorded__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'common_diagnoses': Diagnosis.objects.values('diagnosis_code', 'description').annotate(
                count=Count('id')
            ).order_by('-count')[:10],
            'medication_stats': MedicationHistory.objects.values('status').annotate(
                count=Count('id')
            ),
        }
        
        return Response(report_data)

# ViewSets for API endpoints
class MedicalRecordViewSet(viewsets.ModelViewSet):
    serializer_class = MedicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['record_type', 'priority', 'date_recorded']
    search_fields = ['title', 'description', 'clinical_notes']
    ordering_fields = ['date_recorded', 'created_at', 'priority']
    ordering = ['-date_recorded']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return MedicalRecord.objects.filter(patient__user=user)
        elif user.role == 'doctor':
            return MedicalRecord.objects.filter(doctor__user=user)
        elif user.role == 'admin':
            return MedicalRecord.objects.all()
        else:
            return MedicalRecord.objects.none()

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            last_modified_by=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(last_modified_by=self.request.user)

class AllergyViewSet(viewsets.ModelViewSet):
    serializer_class = AllergySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['allergen_type', 'severity', 'is_active']
    search_fields = ['allergen', 'symptoms', 'notes']
    ordering_fields = ['severity', 'onset_date']
    ordering = ['-severity']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return Allergy.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return Allergy.objects.all()
        else:
            return Allergy.objects.none()

class DiagnosisViewSet(viewsets.ModelViewSet):
    serializer_class = DiagnosisSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_primary']
    search_fields = ['diagnosis_code', 'description', 'notes']
    ordering_fields = ['date_diagnosed', 'status']
    ordering = ['-date_diagnosed']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return Diagnosis.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return Diagnosis.objects.all()
        else:
            return Diagnosis.objects.none()

class MedicationHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = MedicationHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'route']
    search_fields = ['medication_name', 'dosage', 'reason']
    ordering_fields = ['start_date', 'status']
    ordering = ['-start_date']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return MedicationHistory.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return MedicationHistory.objects.all()
        else:
            return MedicationHistory.objects.none()

class VitalSignsRecordViewSet(viewsets.ModelViewSet):
    serializer_class = VitalSignsRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['recorded_date']
    ordering = ['-recorded_date']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return VitalSignsRecord.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return VitalSignsRecord.objects.all()
        else:
            return VitalSignsRecord.objects.none()

class ImmunizationRecordViewSet(viewsets.ModelViewSet):
    serializer_class = ImmunizationRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['vaccine_name', 'manufacturer']
    ordering_fields = ['administration_date', 'next_due_date']
    ordering = ['-administration_date']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return ImmunizationRecord.objects.filter(patient__user=user)
        elif user.role == 'doctor' or user.role == 'admin':
            return ImmunizationRecord.objects.all()
        else:
            return ImmunizationRecord.objects.none()

# Additional API Views for the URLs
class PatientSummaryView(PatientMedicalSummaryView):
    pass

class PatientTimelineView(PatientMedicalTimelineView):
    pass

class HealthOverviewView(HealthOverviewReportView):
    pass

class FileUploadView(MedicalRecordFileUploadView):
    pass