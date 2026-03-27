from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Patient
from django.db.models import Q
from .serializers import PatientSerializer, PatientCreateSerializer, PatientProfileCreateSerializer

from rest_framework.views import APIView

class PatientSelfProfileView(generics.RetrieveUpdateAPIView):
    """
    Patients can view and update their own profile
    """
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user.patient_profile

class PatientListCreateView(generics.ListCreateAPIView): 
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PatientCreateSerializer
        return PatientSerializer

    def get_queryset(self):
        user = self.request.user
        
        # Admins can see all patients
        if user.role == 'ADMIN':
            return Patient.objects.all().select_related('user')
        
        # Doctors can see their patients
        elif user.role == 'DOCTOR':
            try:
                from appointments.models import Appointment
                patient_ids = Appointment.objects.filter(doctor__user=user).values_list('patient_id', flat=True).distinct()
                return Patient.objects.filter(id__in=patient_ids).select_related('user')
            except ImportError:
                # If appointments app doesn't exist, return empty
                return Patient.objects.none()
        
        # Patients can only see themselves
        elif user.role == 'PATIENT':
            return Patient.objects.filter(user=user).select_related('user')
        
        else:
            return Patient.objects.none()

    def perform_create(self, serializer):
        # Only admins can create patient profiles directly
        if self.request.user.role != 'ADMIN':
            raise PermissionDenied("Only administrators can create patient profiles.")
        
        # Check if user already has a patient profile
        user = serializer.validated_data.get('user')
        if user and Patient.objects.filter(user=user).exists():
            raise PermissionDenied("This user already has a patient profile.")
        
        serializer.save()

    def create(self, request, *args, **kwargs):
        # Override to provide better error messages
        try:
            return super().create(request, *args, **kwargs)
        except PermissionDenied as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

class PatientProfileCreateView(generics.CreateAPIView):
    """
    Endpoint for authenticated users to create their patient profile.
    """
    serializer_class = PatientProfileCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Check if user already has a profile
        if hasattr(request.user, 'patient_profile'):
            return Response(
                {'error': 'You already have a patient profile.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Ensure user role is PATIENT
        if request.user.role != 'PATIENT':
            return Response(
                {'error': 'Only users with PATIENT role can create a profile.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'ADMIN':
            return Patient.objects.all().select_related('user')
        elif user.role == 'DOCTOR':
            try:
                from appointments.models import Appointment
                patient_ids = Appointment.objects.filter(doctor__user=user).values_list('patient_id', flat=True).distinct()
                return Patient.objects.filter(id__in=patient_ids).select_related('user')
            except ImportError:
                return Patient.objects.none()
        elif user.role == 'PATIENT':
            return Patient.objects.filter(user=user).select_related('user')
        else:
            return Patient.objects.none()

    def perform_update(self, serializer):
        user = self.request.user
        patient = self.get_object()
        
        # Patients can only update their own profile
        if user.role == 'PATIENT' and patient.user != user:
            raise PermissionDenied("You can only update your own patient profile.")
        
        # Doctors and admins can update any patient profile
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        
        # Only admins can delete patient profiles
        if user.role != 'ADMIN':
            raise PermissionDenied("Only administrators can delete patient profiles.")
        
        # Also delete the associated user (optional - you might want to keep the user)
        instance.user.delete()


class PatientProfileView(generics.RetrieveUpdateAPIView):
    """
    Endpoint for users to access their own patient profile
    """
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        try:
            # Users can only access their own patient profile
            return Patient.objects.select_related('user').get(user=self.request.user)
        except Patient.DoesNotExist:
            raise NotFound({
                'error': 'Patient profile not found',
                'message': 'You need to create a patient profile first.'
            })
    
    def perform_update(self, serializer):
        # Ensure users can only update their own profile
        if serializer.instance.user != self.request.user:
            raise PermissionDenied("You can only update your own profile.")
        serializer.save()


class PatientStatsView(generics.GenericAPIView):
    """
    Get patient statistics (admin only)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        stats = {
            'total_patients': Patient.objects.count(),
            'gender_distribution': self.get_gender_distribution(),
            'age_distribution': self.get_age_distribution(),
            'blood_group_distribution': self.get_blood_group_distribution(),
            'new_patients_today': Patient.objects.filter(
                created_at__date=timezone.now().date()
            ).count(),
        }
        
        return Response(stats)
    
    def get_gender_distribution(self):
        from django.db.models import Count
        return list(Patient.objects.values('gender').annotate(
            count=Count('id')
        ).order_by('gender'))
    
    def get_age_distribution(self):
        # Age groups: Child (0-12), Teen (13-19), Adult (20-59), Senior (60+)
        age_groups = {
            'child': Patient.objects.filter(age__lte=12).count(),
            'teen': Patient.objects.filter(age__range=(13, 19)).count(),
            'adult': Patient.objects.filter(age__range=(20, 59)).count(),
            'senior': Patient.objects.filter(age__gte=60).count(),
        }
        return age_groups
    
    def get_blood_group_distribution(self):
        from django.db.models import Count
        return list(Patient.objects.values('blood_group').annotate(
            count=Count('id')
        ).order_by('blood_group'))

class PatientSearchView(generics.ListAPIView):
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Patient.objects.all()
        
        # Apply filters based on user role
        user = self.request.user
        if user.role == 'PATIENT':
            queryset = queryset.filter(user=user)
        elif user.role == 'DOCTOR':
            # Only show doctor's patients
            pass
        
        # Search by name
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        # Filter by gender
        gender = self.request.query_params.get('gender', None)
        if gender:
            queryset = queryset.filter(gender=gender)
        
        return queryset.select_related('user')