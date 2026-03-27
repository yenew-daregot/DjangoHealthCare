from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import LabRequest, LabTest, LabResult
from .serializers import (
    LabRequestSerializer, LabTestSerializer, LabRequestStatusSerializer, 
    LabResultUploadSerializer, LabRequestCreateSerializer, LabResultSerializer,
    LaboratoristSerializer
)

User = get_user_model()

class LabRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = LabRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = LabRequest.objects.all().select_related(
            'patient', 'doctor', 'test', 'laboratorist'
        ).prefetch_related('result')
        
        # Filter by user role
        user = self.request.user
        if hasattr(user, 'role'):
            if user.role == 'PATIENT':
                # Patients see only their own requests
                if hasattr(user, 'patient'):
                    queryset = queryset.filter(patient=user.patient)
                else:
                    queryset = queryset.none()
            elif user.role == 'DOCTOR':
                # Doctors see requests they made
                if hasattr(user, 'doctor'):
                    queryset = queryset.filter(doctor=user.doctor)
                else:
                    queryset = queryset.none()
            elif user.role == 'LABORATORIST':
                # Laboratorists see assigned requests or unassigned ones
                queryset = queryset.filter(
                    Q(laboratorist=user) | Q(laboratorist__isnull=True)
                )
        
        return queryset.order_by('-requested_date')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LabRequestCreateSerializer
        return LabRequestSerializer
    
    def perform_create(self, serializer):
        serializer.save()

class LabRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = LabRequest.objects.all()
    serializer_class = LabRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

class LabTestListView(generics.ListAPIView):
    queryset = LabTest.objects.all()
    serializer_class = LabTestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        
        if category:
            queryset = queryset.filter(category__icontains=category)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset.order_by('name')

class LabTestDetailView(generics.RetrieveAPIView):
    queryset = LabTest.objects.all()
    serializer_class = LabTestSerializer
    permission_classes = [permissions.IsAuthenticated]

class PatientLabRequestsView(generics.ListAPIView):
    serializer_class = LabRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        return LabRequest.objects.filter(patient_id=patient_id).select_related(
            'patient', 'doctor', 'test', 'laboratorist'
        ).prefetch_related('result').order_by('-requested_date')

class DoctorLabRequestsView(generics.ListAPIView):
    serializer_class = LabRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        doctor_id = self.kwargs['doctor_id']
        return LabRequest.objects.filter(doctor_id=doctor_id).select_related(
            'patient', 'doctor', 'test', 'laboratorist'
        ).prefetch_related('result').order_by('-requested_date')

class LaboratoristLabRequestsView(generics.ListAPIView):
    serializer_class = LabRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        laboratorist_id = self.kwargs['laboratorist_id']
        return LabRequest.objects.filter(
            Q(laboratorist_id=laboratorist_id) | Q(laboratorist__isnull=True)
        ).select_related(
            'patient', 'doctor', 'test', 'laboratorist'
        ).prefetch_related('result').order_by('-requested_date')

class UpdateLabRequestStatusView(generics.UpdateAPIView):
    queryset = LabRequest.objects.all()
    serializer_class = LabRequestStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

class AssignLaboratoristView(generics.UpdateAPIView):
    queryset = LabRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        laboratorist_id = request.data.get('laboratorist_id')
        
        if laboratorist_id:
            try:
                laboratorist = User.objects.get(id=laboratorist_id, role='LABORATORIST')
                instance.laboratorist = laboratorist
                instance.status = 'assigned'
                instance.assigned_date = timezone.now()
                instance.save()
                
                serializer = LabRequestSerializer(instance)
                return Response(serializer.data)
            except User.DoesNotExist:
                return Response(
                    {'error': 'Laboratorist not found'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            {'error': 'Laboratorist ID required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

class LabResultCreateUpdateView(generics.CreateAPIView, generics.UpdateAPIView):
    queryset = LabResult.objects.all()
    serializer_class = LabResultUploadSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_object(self):
        lab_request_id = self.kwargs.get('lab_request_id')
        lab_request = get_object_or_404(LabRequest, id=lab_request_id)
        result, created = LabResult.objects.get_or_create(lab_request=lab_request)
        return result
    
    def perform_create(self, serializer):
        lab_request_id = self.kwargs.get('lab_request_id')
        lab_request = get_object_or_404(LabRequest, id=lab_request_id)
        
        # Update lab request status
        lab_request.status = 'completed'
        lab_request.completed_date = timezone.now()
        lab_request.save()
        
        serializer.save(lab_request=lab_request, created_by=self.request.user)
    
    def perform_update(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        
        # Update lab request status
        instance.lab_request.status = 'completed'
        instance.lab_request.completed_date = timezone.now()
        instance.lab_request.save()

class LaboratoristListView(generics.ListAPIView):
    serializer_class = LaboratoristSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return User.objects.filter(role='LABORATORIST', is_active=True)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_users(request):
    """Search for patients, doctors, or laboratorists by name, email, or ID"""
    query = request.GET.get('q', '')
    user_type = request.GET.get('type', '')  # 'patient', 'doctor', 'laboratorist'
    
    if not query:
        return Response({'results': []})
    
    results = []
    
    if user_type == 'laboratorist' or not user_type:
        # Search laboratorists
        laboratorists = User.objects.filter(
            role='LABORATORIST',
            is_active=True
        ).filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(username__icontains=query)
        )[:10]
        
        for lab in laboratorists:
            results.append({
                'id': lab.id,
                'name': f"{lab.first_name} {lab.last_name}".strip() or lab.username,
                'email': lab.email,
                'type': 'laboratorist'
            })
    
    return Response({'results': results})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def lab_dashboard_stats(request):
    """Get dashboard statistics for lab management"""
    user = request.user
    
    if hasattr(user, 'role') and user.role == 'LABORATORIST':
        # Stats for laboratorist
        total_assigned = LabRequest.objects.filter(laboratorist=user).count()
        pending = LabRequest.objects.filter(
            laboratorist=user, 
            status__in=['assigned', 'sample_collected', 'in_progress']
        ).count()
        completed_today = LabRequest.objects.filter(
            laboratorist=user,
            status='completed',
            completed_date__date=timezone.now().date()
        ).count()
        
        return Response({
            'total_assigned': total_assigned,
            'pending': pending,
            'completed_today': completed_today,
            'unassigned': LabRequest.objects.filter(laboratorist__isnull=True).count()
        })
    
    elif hasattr(user, 'role') and user.role == 'DOCTOR':
        # Stats for doctor
        if hasattr(user, 'doctor'):
            total_requests = LabRequest.objects.filter(doctor=user.doctor).count()
            pending = LabRequest.objects.filter(
                doctor=user.doctor,
                status__in=['requested', 'assigned', 'sample_collected', 'in_progress']
            ).count()
            completed = LabRequest.objects.filter(
                doctor=user.doctor,
                status='completed'
            ).count()
            
            return Response({
                'total_requests': total_requests,
                'pending': pending,
                'completed': completed
            })
    
    return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)