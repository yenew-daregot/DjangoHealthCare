from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.http import HttpResponse
from django.db.models import Count
from rest_framework.views import APIView
from django.db.models import Q, Count, Avg, Max, Min
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
from .models import EmergencyProtocol 
from .serializers import EmergencyStatisticsSerializer
import json
from .models import (
    EmergencyContact, EmergencyRequest, EmergencyResponseTeam,
    EmergencyResponse, EmergencyAlert, EmergencyProtocol
)
from .serializers import (
    EmergencyContactSerializer, EmergencyRequestSerializer,
    EmergencyRequestDetailSerializer, EmergencyResponseTeamSerializer,
    EmergencyResponseSerializer, EmergencyAlertSerializer,
    EmergencyProtocolSerializer,
    CreateEmergencyRequestSerializer, UpdateEmergencyStatusSerializer,
    AssignTeamSerializer, UpdateVitalsSerializer, SOSAlertSerializer,
    EmergencyLocationSerializer
)
from patients.models import Patient
from doctors.models import Doctor

from rest_framework.permissions import IsAdminUser
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

class AdminEmergencyRequestListView(ListAPIView):
    """Admin view for listing all emergency requests"""
    permission_classes = [IsAdminUser]
    serializer_class = EmergencyRequestSerializer
    queryset = EmergencyRequest.objects.all().order_by('-created_at')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'priority', 'emergency_type']
    search_fields = [
        'patient__user__first_name',
        'patient__user__last_name', 
        'request_id',
        'location',
        'patient__user__email'
    ]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        
        # Add statistics to response
        queryset = self.filter_queryset(self.get_queryset())
        total = queryset.count()
        active = queryset.filter(status__in=['pending', 'acknowledged', 'dispatched', 'en_route', 'arrived']).count()
        critical = queryset.filter(priority='critical').count()
        
        response.data = {
            'results': response.data,
            'stats': {
                'total': total,
                'active': active,
                'critical': critical,
                'responded': queryset.filter(acknowledged_at__isnull=False).count(),
                'averageResponseTime': self.calculate_average_response_time(queryset)
            }
        }
        
        return response
    
    def calculate_average_response_time(self, queryset):
        responded = queryset.filter(acknowledged_at__isnull=False)
        if not responded.exists():
            return 0
        
        total_time = sum(
            (emergency.acknowledged_at - emergency.created_at).total_seconds()
            for emergency in responded
        )
        return round(total_time / responded.count() / 60, 1)  # Convert to minutes

class AdminEmergencyRequestDetailView(RetrieveAPIView):
    """Admin view for emergency request details"""
    permission_classes = [IsAdminUser]
    serializer_class = EmergencyRequestDetailSerializer
    queryset = EmergencyRequest.objects.all()

class AdminUpdateEmergencyStatusView(UpdateAPIView):
    """Admin view to update emergency status"""
    permission_classes = [IsAdminUser]
    serializer_class = UpdateEmergencyStatusSerializer
    queryset = EmergencyRequest.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Update status and timestamps
        new_status = serializer.validated_data.get('status')
        if new_status:
            instance.status = new_status
            
            now = timezone.now()
            if new_status == 'acknowledged' and not instance.acknowledged_at:
                instance.acknowledged_at = now
            elif new_status == 'dispatched' and not instance.dispatched_at:
                instance.dispatched_at = now
            elif new_status == 'arrived' and not instance.arrived_at:
                instance.arrived_at = now
            elif new_status == 'completed' and not instance.completed_at:
                instance.completed_at = now
            
            instance.save()
        
        return Response(EmergencyRequestDetailSerializer(instance).data)

class AdminAssignTeamView(UpdateAPIView):
    """Admin view to assign team to emergency"""
    permission_classes = [IsAdminUser]
    serializer_class = AssignTeamSerializer
    queryset = EmergencyRequest.objects.all()

class AdminUpdateEmergencyLocationView(UpdateAPIView):
    """Admin view to update emergency location"""
    permission_classes = [IsAdminUser]
    serializer_class = EmergencyLocationSerializer
    queryset = EmergencyRequest.objects.all()

class AdminEmergencyStatisticsView(APIView):
    """Admin view for emergency statistics"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Calculate comprehensive statistics
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        total_emergencies = EmergencyRequest.objects.count()
        
        # Today's stats
        todays_emergencies = EmergencyRequest.objects.filter(created_at__date=today)
        
        # Response time stats
        responded_emergencies = EmergencyRequest.objects.filter(acknowledged_at__isnull=False)
        avg_response_time = 0
        if responded_emergencies.exists():
            total_time = sum(
                (emergency.acknowledged_at - emergency.created_at).total_seconds()
                for emergency in responded_emergencies
            )
            avg_response_time = round(total_time / responded_emergencies.count() / 60, 1)
        
        # Status breakdown
        status_breakdown = {
            'pending': EmergencyRequest.objects.filter(status='pending').count(),
            'acknowledged': EmergencyRequest.objects.filter(status='acknowledged').count(),
            'dispatched': EmergencyRequest.objects.filter(status='dispatched').count(),
            'en_route': EmergencyRequest.objects.filter(status='en_route').count(),
            'arrived': EmergencyRequest.objects.filter(status='arrived').count(),
            'completed': EmergencyRequest.objects.filter(status='completed').count(),
            'cancelled': EmergencyRequest.objects.filter(status='cancelled').count(),
        }
        
        # Priority breakdown
        priority_breakdown = {
            'critical': EmergencyRequest.objects.filter(priority='critical').count(),
            'high': EmergencyRequest.objects.filter(priority='high').count(),
            'medium': EmergencyRequest.objects.filter(priority='medium').count(),
            'low': EmergencyRequest.objects.filter(priority='low').count(),
        }
        
        # Type breakdown
        type_breakdown = EmergencyRequest.objects.values('emergency_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Recent emergencies (last 10)
        recent_emergencies = EmergencyRequest.objects.all().order_by('-created_at')[:10]
        recent_serializer = EmergencyRequestSerializer(recent_emergencies, many=True)
        
        stats = {
            'total': total_emergencies,
            'today': todays_emergencies.count(),
            'active': EmergencyRequest.objects.filter(
                status__in=['pending', 'acknowledged', 'dispatched', 'en_route', 'arrived']
            ).count(),
            'critical': EmergencyRequest.objects.filter(priority='critical').count(),
            'responded': responded_emergencies.count(),
            'averageResponseTime': avg_response_time,
            'statusBreakdown': status_breakdown,
            'priorityBreakdown': priority_breakdown,
            'typeBreakdown': list(type_breakdown),
            'recentEmergencies': recent_serializer.data,
        }
        
        return Response(stats)

class AdminEmergencyExportView(APIView):
    """Admin view to export emergency data"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        format_type = request.GET.get('format', 'csv')
        report_type = request.GET.get('report_type', 'emergencies_summary')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Filter queryset based on date range
        queryset = EmergencyRequest.objects.all()
        
        if start_date and end_date:
            queryset = queryset.filter(
                created_at__date__range=[start_date, end_date]
            )
        
        # Create CSV content
        import csv
        from io import StringIO
        
        # Create CSV
        csvfile = StringIO()
        csvwriter = csv.writer(csvfile)
        
        # Write headers
        headers = [
            'ID', 'Patient Name', 'Patient Email', 'Emergency Type', 
            'Location', 'Priority', 'Status', 'Created At', 
            'Acknowledged At', 'Dispatched At', 'Completed At', 'Response Time (min)'
        ]
        csvwriter.writerow(headers)
        
        # Write data rows
        for emergency in queryset:
            response_time = 'N/A'
            if emergency.acknowledged_at:
                response_time = round(
                    (emergency.acknowledged_at - emergency.created_at).total_seconds() / 60, 
                    1
                )
            
            row = [
                emergency.request_id,
                f"{emergency.patient.user.first_name} {emergency.patient.user.last_name}",
                emergency.patient.user.email,
                emergency.emergency_type,
                emergency.location,
                emergency.priority,
                emergency.status,
                emergency.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                emergency.acknowledged_at.strftime('%Y-%m-%d %H:%M:%S') if emergency.acknowledged_at else 'N/A',
                emergency.dispatched_at.strftime('%Y-%m-%d %H:%M:%S') if emergency.dispatched_at else 'N/A',
                emergency.completed_at.strftime('%Y-%m-%d %H:%M:%S') if emergency.completed_at else 'N/A',
                response_time
            ]
            csvwriter.writerow(row)
        
        # Create response
        response = HttpResponse(csvfile.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="emergencies_export_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        return response

# Emergency Contact Views
class EmergencyContactListCreateView(generics.ListCreateAPIView):
    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'PATIENT':
            return EmergencyContact.objects.filter(patient__user=user)
        elif user.role in ['DOCTOR', 'ADMIN']:
            return EmergencyContact.objects.all()
        else:
            return EmergencyContact.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role == 'PATIENT':
            try:
                patient = Patient.objects.get(user=self.request.user)
                serializer.save(patient=patient)
            except Patient.DoesNotExist:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'error': 'Patient profile not found. Please complete your profile first.'})
        else:
            serializer.save()

class EmergencyContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'PATIENT':
            return EmergencyContact.objects.filter(patient__user=user)
        elif user.role in ['DOCTOR', 'ADMIN']:
            return EmergencyContact.objects.all()
        else:
            return EmergencyContact.objects.none()

class PatientEmergencyContactsView(generics.ListAPIView):
    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        return EmergencyContact.objects.filter(patient_id=patient_id)

class SetPrimaryContactView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        contact = get_object_or_404(EmergencyContact, pk=pk)
        
        # Verify the contact belongs to the patient making the request
        if request.user.role == 'PATIENT' and contact.patient.user != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Set all contacts as non-primary first
        EmergencyContact.objects.filter(patient=contact.patient).update(is_primary=False)
        
        # Set this contact as primary
        contact.is_primary = True
        contact.save()
        
        return Response({'status': 'Contact set as primary'})

class EmergencyRequestListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateEmergencyRequestSerializer
        return EmergencyRequestSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = EmergencyRequest.objects.all().order_by('-created_at')
        
        # Apply filters from query parameters
        status = self.request.GET.get('status')
        priority = self.request.GET.get('priority')
        emergency_type = self.request.GET.get('type')
        search = self.request.GET.get('search')
        
        if status and status != 'all':
            queryset = queryset.filter(status=status)
        
        if priority and priority != 'all':
            queryset = queryset.filter(priority=priority)
        
        if emergency_type and emergency_type != 'all':
            queryset = queryset.filter(emergency_type=emergency_type)
        
        if search:
            queryset = queryset.filter(
                Q(patient__user__first_name__icontains=search) |
                Q(patient__user__last_name__icontains=search) |
                Q(request_id__icontains=search) |
                Q(location__icontains=search) |
                Q(patient__user__email__icontains=search)
            )
        
        return queryset

    def list(self, request, *args, **kwargs):
        # Get the paginated queryset
        queryset = self.filter_queryset(self.get_queryset())
        
        # Calculate statistics
        total = queryset.count()
        active = queryset.filter(
            status__in=['pending', 'acknowledged', 'dispatched', 'en_route', 'arrived']
        ).count()
        critical = queryset.filter(priority='critical').count()
        
        # Calculate average response time
        responded_emergencies = queryset.filter(acknowledged_at__isnull=False)
        average_response_time = 0
        if responded_emergencies.exists():
            total_time = sum(
                (emergency.acknowledged_at - emergency.created_at).total_seconds()
                for emergency in responded_emergencies
            )
            average_response_time = total_time / responded_emergencies.count() / 60  # Convert to minutes
        
        # Paginate the queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'results': serializer.data,
                'stats': {
                    'total': total,
                    'active': active,
                    'critical': critical,
                    'responded': responded_emergencies.count(),
                    'averageResponseTime': round(average_response_time, 1)
                }
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'stats': {
                'total': total,
                'active': active,
                'critical': critical,
                'responded': responded_emergencies.count(),
                'averageResponseTime': round(average_response_time, 1)
            }
        })

    def perform_create(self, serializer):
        if self.request.user.role == 'PATIENT':
            try:
                patient = Patient.objects.get(user=self.request.user)
                serializer.save(patient=patient)
            except Patient.DoesNotExist:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'error': 'Patient profile not found. Please complete your profile first.'})
        else:
            serializer.save()

class EmergencyRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmergencyRequestDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'PATIENT':
            return EmergencyRequest.objects.filter(patient__user=user)
        elif user.role in ['DOCTOR', 'ADMIN']:
            return EmergencyRequest.objects.all()
        else:
            return EmergencyRequest.objects.none()

class EmergencyRequestByIDView(generics.RetrieveAPIView):
    serializer_class = EmergencyRequestDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'request_id'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'PATIENT':
            return EmergencyRequest.objects.filter(patient__user=user)
        elif user.role in ['DOCTOR', 'ADMIN']:
            return EmergencyRequest.objects.all()
        else:
            return EmergencyRequest.objects.none()

class EmergencyResponseListCreateView(generics.ListCreateAPIView):
    serializer_class = EmergencyResponseSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = EmergencyResponse.objects.all()

class EmergencyResponseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmergencyResponseSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = EmergencyResponse.objects.all()

class EmergencyRequestResponseView(generics.RetrieveAPIView):
    serializer_class = EmergencyResponseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        request_id = self.kwargs['request_id']
        return get_object_or_404(EmergencyResponse, emergency_request_id=request_id)


class PatientEmergencyRequestsView(generics.ListAPIView):
    serializer_class = EmergencyRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        return EmergencyRequest.objects.filter(patient_id=patient_id)

class UpdateEmergencyStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        emergency = get_object_or_404(EmergencyRequest, pk=pk)
        serializer = UpdateEmergencyStatusSerializer(data=request.data)
        
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            notes = serializer.validated_data.get('notes', '')
            
            # Update status and set appropriate timestamp
            emergency.status = new_status
            if notes:
                emergency.response_notes = notes
            
            now = timezone.now()
            if new_status == 'acknowledged' and not emergency.acknowledged_at:
                emergency.acknowledged_at = now
            elif new_status == 'dispatched' and not emergency.dispatched_at:
                emergency.dispatched_at = now
            elif new_status == 'arrived' and not emergency.arrived_at:
                emergency.arrived_at = now
            elif new_status == 'completed' and not emergency.completed_at:
                emergency.completed_at = now
            
            emergency.save()
            
            return Response(EmergencyRequestDetailSerializer(emergency).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AssignResponseTeamView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        emergency = get_object_or_404(EmergencyRequest, pk=pk)
        serializer = AssignTeamSerializer(data=request.data)
        
        if serializer.is_valid():
            team_member_id = serializer.validated_data.get('team_member_id')
            doctor_id = serializer.validated_data.get('doctor_id')
            
            if team_member_id:
                team_member = get_object_or_404(EmergencyResponseTeam, pk=team_member_id)
                emergency.first_responder = team_member.user
                emergency.status = 'dispatched'
                emergency.dispatched_at = timezone.now()
            
            if doctor_id:
                doctor = get_object_or_404(Doctor, pk=doctor_id)
                emergency.assigned_doctor = doctor
            
            emergency.save()
            
            return Response(EmergencyRequestDetailSerializer(emergency).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ActiveEmergenciesView(generics.ListAPIView):
    serializer_class = EmergencyRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        active_statuses = ['pending', 'acknowledged', 'dispatched', 'en_route', 'arrived', 'transporting']
        return EmergencyRequest.objects.filter(status__in=active_statuses)

class CriticalEmergenciesView(generics.ListAPIView):
    serializer_class = EmergencyRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyRequest.objects.filter(priority='critical', status__in=['pending', 'acknowledged'])

# Emergency Response Team Views
class EmergencyResponseTeamListView(generics.ListAPIView):
    serializer_class = EmergencyResponseTeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyResponseTeam.objects.filter(is_active=True)

class EmergencyResponseTeamDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = EmergencyResponseTeamSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = EmergencyResponseTeam.objects.all()

class AvailableResponseTeamView(generics.ListAPIView):
    serializer_class = EmergencyResponseTeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyResponseTeam.objects.filter(
            is_active=True,
            status__in=['available', 'on_call']
        )

class UpdateTeamMemberStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        team_member = get_object_or_404(EmergencyResponseTeam, pk=pk)
        
        new_status = request.data.get('status')
        location = request.data.get('location')
        
        if new_status in dict(EmergencyResponseTeam.STATUS_CHOICES):
            team_member.status = new_status
        
        if location:
            team_member.current_location = location
        
        team_member.save()
        
        return Response(EmergencyResponseTeamSerializer(team_member).data)

# Emergency Alert Views
class EmergencyAlertListCreateView(generics.ListCreateAPIView):
    serializer_class = EmergencyAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'PATIENT':
            return EmergencyAlert.objects.filter(patient__user=user)
        elif user.role in ['DOCTOR', 'ADMIN']:
            return EmergencyAlert.objects.all()
        else:
            return EmergencyAlert.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role == 'PATIENT':
            try:
                patient = Patient.objects.get(user=self.request.user)
                serializer.save(patient=patient)
            except Patient.DoesNotExist:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'error': 'Patient profile not found. Please complete your profile first.'})
        else:
            serializer.save()

class EmergencyAlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmergencyAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'PATIENT':
            return EmergencyAlert.objects.filter(patient__user=user)
        elif user.role in ['DOCTOR', 'ADMIN']:
            return EmergencyAlert.objects.all()
        else:
            return EmergencyAlert.objects.none()

class PatientEmergencyAlertsView(generics.ListAPIView):
    serializer_class = EmergencyAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        return EmergencyAlert.objects.filter(patient_id=patient_id)

class VerifyEmergencyAlertView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        alert = get_object_or_404(EmergencyAlert, pk=pk)
        alert.is_verified = True
        alert.verified_by = request.user
        alert.save()
        
        # Create emergency request from verified alert
        emergency_request = EmergencyRequest.objects.create(
            patient=alert.patient,
            location=alert.location,
            latitude=alert.latitude,
            longitude=alert.longitude,
            description=f"Auto-generated from {alert.alert_type} alert",
            emergency_type=alert.alert_type,
            priority='high' if alert.alert_type in ['sos', 'heart_attack', 'stroke'] else 'medium'
        )
        
        # Notify emergency contacts
        from .tasks import notify_emergency_contacts_async
        notify_emergency_contacts_async.delay(alert.patient.id, emergency_request.id)
        
        return Response({
            'alert': EmergencyAlertSerializer(alert).data,
            'emergency_request': EmergencyRequestSerializer(emergency_request).data
        })

class SOSAlertView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SOSAlertSerializer(data=request.data)
        
        if serializer.is_valid():
            if request.user.role == 'PATIENT':
                try:
                    patient = Patient.objects.get(user=request.user)
                except Patient.DoesNotExist:
                    return Response(
                        {'error': 'Patient profile not found. Please complete your profile first.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create emergency alert
                alert = EmergencyAlert.objects.create(
                    patient=patient,
                    alert_type='sos',
                    location=serializer.validated_data['location'],
                    latitude=serializer.validated_data.get('latitude'),
                    longitude=serializer.validated_data.get('longitude'),
                    message=serializer.validated_data.get('message', 'SOS Emergency'),
                    is_auto_generated=False
                )
                
                # Create emergency request
                emergency_request = EmergencyRequest.objects.create(
                    patient=patient,
                    location=serializer.validated_data['location'],
                    latitude=serializer.validated_data.get('latitude'),
                    longitude=serializer.validated_data.get('longitude'),
                    description=serializer.validated_data.get('message', 'SOS Emergency - Immediate assistance required'),
                    emergency_type='sos',
                    priority='critical',
                    status='pending'
                )
                
                # Notify emergency contacts
                from .tasks import notify_emergency_contacts_async
                notify_emergency_contacts_async.delay(patient.id, emergency_request.id)
                
                return Response({
                    'alert': EmergencyAlertSerializer(alert).data,
                    'emergency_request': EmergencyRequestSerializer(emergency_request).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': 'Only patients can send SOS alerts'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Emergency Protocol Views
class EmergencyProtocolListView(generics.ListAPIView):
    serializer_class = EmergencyProtocolSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = EmergencyProtocol.objects.filter(is_active=True)

class EmergencyProtocolDetailView(generics.RetrieveAPIView):
    serializer_class = EmergencyProtocolSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = EmergencyProtocol.objects.all()

class ProtocolsByTypeView(generics.ListAPIView):
    serializer_class = EmergencyProtocolSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        protocol_type = self.kwargs['protocol_type']
        return EmergencyProtocol.objects.filter(
            protocol_type=protocol_type,
            is_active=True
        )

# Statistics and Reports
class DailyEmergencyStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        
        stats = {
            'date': today,
            'total_emergencies': EmergencyRequest.objects.filter(created_at__date=today).count(),
            'responded_emergencies': EmergencyRequest.objects.filter(
                created_at__date=today,
                status__in=['completed', 'handed_over']
            ).count(),
            'critical_cases': EmergencyRequest.objects.filter(
                created_at__date=today,
                priority='critical'
            ).count(),
            'average_response_time': self.calculate_average_response_time(today),
            'most_common_emergency': self.get_most_common_emergency_type(today),
        }
        
        return Response(stats)

    def calculate_average_response_time(self, date):
        responded_emergencies = EmergencyRequest.objects.filter(
            created_at__date=date,
            acknowledged_at__isnull=False
        )
        
        if responded_emergencies.exists():
            total_time = sum(
                (emergency.acknowledged_at - emergency.created_at).total_seconds()
                for emergency in responded_emergencies
            )
            return total_time / responded_emergencies.count()
        return 0

    def get_most_common_emergency_type(self, date):
        result = EmergencyRequest.objects.filter(
            created_at__date=date
        ).values('emergency_type').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        return result['emergency_type'] if result else 'None'

class MonthlyEmergencyStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        first_day = today.replace(day=1)
        
        stats = {
            'month': today.strftime('%Y-%m'),
            'total_emergencies': EmergencyRequest.objects.filter(
                created_at__date__gte=first_day
            ).count(),
            'responded_emergencies': EmergencyRequest.objects.filter(
                created_at__date__gte=first_day,
                status__in=['completed', 'handed_over']
            ).count(),
            'success_rate': self.calculate_success_rate(first_day),
            'emergency_types': self.get_emergency_type_breakdown(first_day),
            'response_time_trend': self.get_response_time_trend(first_day),
        }
        
        return Response(stats)

    def calculate_success_rate(self, first_day):
        total = EmergencyRequest.objects.filter(created_at__date__gte=first_day).count()
        successful = EmergencyRequest.objects.filter(
            created_at__date__gte=first_day,
            status='completed'
        ).count()
        
        return (successful / total * 100) if total > 0 else 0

    def get_emergency_type_breakdown(self, first_day):
        return list(
            EmergencyRequest.objects.filter(
                created_at__date__gte=first_day
            ).values('emergency_type').annotate(
                count=Count('id')
            ).order_by('-count')
        )

    def get_response_time_trend(self, first_day):
        return {"trend": "stable", "average_time": 45.2}

class ResponseTimeReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        days = int(request.GET.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        response_times = EmergencyRequest.objects.filter(
            created_at__date__gte=start_date,
            acknowledged_at__isnull=False
        ).extra({
            'response_time': 'EXTRACT(EPOCH FROM (acknowledged_at - created_at))'
        }).values('created_at__date').annotate(
            avg_response_time=Avg('response_time'),
            min_response_time=Min('response_time'),
            max_response_time=Max('response_time')
        ).order_by('created_at__date')
        
        return Response(list(response_times))

class EmergencyTypeReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        days = int(request.GET.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        type_breakdown = EmergencyRequest.objects.filter(
            created_at__date__gte=start_date
        ).values('emergency_type').annotate(
            count=Count('id'),
            avg_response_time=Avg('response_time')
        ).order_by('-count')
        
        return Response(list(type_breakdown))

# Real-time Emergency Features
class UpdateEmergencyLocationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        emergency = get_object_or_404(EmergencyRequest, pk=pk)
        serializer = EmergencyLocationSerializer(data=request.data)
        
        if serializer.is_valid():
            emergency.location = serializer.validated_data['location']
            emergency.latitude = serializer.validated_data.get('latitude')
            emergency.longitude = serializer.validated_data.get('longitude')
            emergency.location_notes = serializer.validated_data.get('location_notes', '')
            emergency.save()
            
            return Response(EmergencyRequestDetailSerializer(emergency).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateEmergencyVitalsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        emergency = get_object_or_404(EmergencyRequest, pk=pk)
        serializer = UpdateVitalsSerializer(data=request.data)
        
        if serializer.is_valid():
            for field, value in serializer.validated_data.items():
                if value is not None:
                    setattr(emergency, field, value)
            
            emergency.save()
            
            return Response(EmergencyRequestDetailSerializer(emergency).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AddEmergencyNoteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        emergency = get_object_or_404(EmergencyRequest, pk=pk)
        note = request.data.get('note', '')
        note_type = request.data.get('type', 'general')
        
        if not note:
            return Response(
                {'error': 'Note content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if note_type == 'medical':
            emergency.medical_notes += f"\n{timestamp}: {note}"
        elif note_type == 'response':
            emergency.response_notes += f"\n{timestamp}: {note}"
        else:
            emergency.response_notes += f"\n{timestamp}: {note}"
        
        emergency.save()
        
        return Response({'status': 'Note added successfully'})

# Mobile App Endpoints
class QuickSOSView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role != 'PATIENT':
            return Response(
                {'error': 'Only patients can use Quick SOS'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            return Response(
                {'error': 'Patient profile not found. Please complete your profile first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create emergency with minimal information
        emergency = EmergencyRequest.objects.create(
            patient=patient,
            location='Auto-detected location',
            description='Quick SOS emergency - immediate assistance required',
            emergency_type='sos',
            priority='critical'
        )
        
        # Notify emergency contacts
        try:
            from .tasks import notify_emergency_contacts_async
            notify_emergency_contacts_async.delay(patient.id, emergency.id)
        except Exception as e:
            # Log the error but don't fail the emergency request
            print(f"Failed to send emergency notifications: {e}")
        
        return Response({
            'emergency_id': emergency.request_id,
            'message': 'Emergency assistance has been requested',
            'response_time': 'Help is on the way'
        })

class NearbyHospitalsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        latitude = request.GET.get('lat')
        longitude = request.GET.get('lng')
        radius = float(request.GET.get('radius', 10))  # km
        
        if not latitude or not longitude:
            return Response(
                {'error': 'Latitude and longitude are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lat = float(latitude)
            lng = float(longitude)
        except ValueError:
            return Response(
                {'error': 'Invalid coordinates'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find nearby hospitals from database
        hospitals = Hospital.find_nearest_hospitals(lat, lng, limit=10)
        
        # Enhanced hospital data with route information
        enhanced_hospitals = []
        for hospital in hospitals:
            distance_km = hospital.calculate_distance_to(lat, lng)
            
            # Estimate travel time (basic calculation)
            # In production, this would use Google Maps API
            estimated_time_minutes = max(5, int(distance_km * 2.5))  # Rough estimate
            
            hospital_data = {
                'id': hospital.id,
                'name': hospital.name,
                'address': hospital.address,
                'phone_number': hospital.phone_number,
                'emergency_phone': hospital.emergency_phone,
                'hospital_type': hospital.hospital_type,
                'has_emergency_department': hospital.has_emergency_department,
                'has_trauma_center': hospital.has_trauma_center,
                'trauma_level': hospital.trauma_level,
                'current_wait_time': hospital.current_wait_time,
                'accepts_ambulances': hospital.accepts_ambulances,
                'is_on_diversion': hospital.is_on_diversion,
                'location': {
                    'latitude': float(hospital.latitude) if hospital.latitude else None,
                    'longitude': float(hospital.longitude) if hospital.longitude else None
                },
                'distance': {
                    'km': round(distance_km, 1),
                    'text': f"{distance_km:.1f} km"
                },
                'estimated_travel_time': {
                    'minutes': estimated_time_minutes,
                    'text': f"{estimated_time_minutes} min"
                },
                'google_maps_url': f"https://www.google.com/maps/dir/{lat},{lng}/{hospital.latitude},{hospital.longitude}",
                'navigation_url': f"https://www.google.com/maps/dir/?api=1&origin={lat},{lng}&destination={hospital.latitude},{hospital.longitude}&travelmode=driving&dir_action=navigate"
            }
            enhanced_hospitals.append(hospital_data)
        
        return Response(enhanced_hospitals)

class EmergencyGuideView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        guide = {
            'cardiac_arrest': {
                'steps': [
                    'Check for responsiveness',
                    'Call emergency services',
                    'Begin CPR if trained',
                    'Use AED if available'
                ],
                'do_not': [
                    'Leave the person alone',
                    'Stop CPR unless exhausted or help arrives'
                ]
            },
            'choking': {
                'steps': [
                    'Ask if they can speak or cough',
                    'Perform abdominal thrusts if conscious',
                    'Call emergency services if obstruction continues'
                ]
            },
            'bleeding': {
                'steps': [
                    'Apply direct pressure',
                    'Elevate the injury',
                    'Call emergency services for severe bleeding'
                ]
            }
        }
        
        return Response(guide)

class EmergencyStatisticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Calculate comprehensive statistics
        total_emergencies = EmergencyRequest.objects.count()
        
        active_emergencies = EmergencyRequest.objects.filter(
            status__in=['pending', 'acknowledged', 'dispatched', 'en_route', 'arrived']
        ).count()
        
        critical_emergencies = EmergencyRequest.objects.filter(priority='critical').count()
        
        # Calculate average response time
        responded_emergencies = EmergencyRequest.objects.filter(acknowledged_at__isnull=False)
        avg_response_time = 0
        if responded_emergencies.exists():
            total_time = sum(
                (emergency.acknowledged_at - emergency.created_at).total_seconds()
                for emergency in responded_emergencies
            )
            avg_response_time = round(total_time / responded_emergencies.count() / 60, 1)  # Convert to minutes
        
        # Status breakdown
        status_breakdown = EmergencyRequest.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Priority breakdown
        priority_breakdown = EmergencyRequest.objects.values('priority').annotate(
            count=Count('id')
        ).order_by('priority')
        
        # Type breakdown
        type_breakdown = EmergencyRequest.objects.values('emergency_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        stats = {
            'total': total_emergencies,
            'active': active_emergencies,
            'critical': critical_emergencies,
            'responded': responded_emergencies.count(),
            'averageResponseTime': avg_response_time,
            'statusBreakdown': list(status_breakdown),
            'priorityBreakdown': list(priority_breakdown),
            'typeBreakdown': list(type_breakdown),
        }
        
        return Response(stats)

class ExportEmergencyReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get date range from query params
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Filter emergencies
        emergencies = EmergencyRequest.objects.all()
        
        if start_date and end_date:
            emergencies = emergencies.filter(
                created_at__date__range=[start_date, end_date]
            )
        
        # Create CSV
        import csv
        from io import StringIO
        
        csvfile = StringIO()
        csvwriter = csv.writer(csvfile)
        
        # Write headers
        headers = [
            'ID', 'Patient Name', 'Patient Email', 'Emergency Type', 
            'Location', 'Priority', 'Status', 'Created At', 
            'Acknowledged At', 'Response Time (min)'
        ]
        csvwriter.writerow(headers)
        
        # Write data rows
        for emergency in emergencies:
            response_time = 'N/A'
            if emergency.acknowledged_at:
                response_time = round(
                    (emergency.acknowledged_at - emergency.created_at).total_seconds() / 60, 
                    1
                )
            
            patient_name = f"{emergency.patient.user.first_name} {emergency.patient.user.last_name}"
            
            row = [
                emergency.request_id,
                patient_name,
                emergency.patient.user.email,
                emergency.emergency_type,
                emergency.location,
                emergency.priority,
                emergency.status,
                emergency.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                emergency.acknowledged_at.strftime('%Y-%m-%d %H:%M:%S') if emergency.acknowledged_at else 'N/A',
                response_time
            ]
            csvwriter.writerow(row)
        # Create HTTP response
        from django.http import HttpResponse
        response = HttpResponse(csvfile.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="emergency_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        return response

class NearbyHospitalsEnhancedView(APIView):
    """Enhanced hospital search with Google Maps integration"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        latitude = request.GET.get('lat')
        longitude = request.GET.get('lng')
        radius = float(request.GET.get('radius', 10))  # km
        
        if not latitude or not longitude:
            return Response(
                {'error': 'Latitude and longitude are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lat = float(latitude)
            lng = float(longitude)
        except ValueError:
            return Response(
                {'error': 'Invalid coordinates'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find nearby hospitals
        hospitals = Hospital.find_nearest_hospitals(lat, lng, limit=10)
        
        # Enhanced hospital data with detailed route information
        enhanced_hospitals = []
        for hospital in hospitals:
            distance_km = hospital.calculate_distance_to(lat, lng)
            
            # Enhanced travel time calculation with traffic consideration
            base_time = distance_km * 2.5  # Base time in minutes
            traffic_factor = 1.2  # 20% traffic delay
            estimated_time = max(5, int(base_time * traffic_factor))
            
            # Calculate arrival time
            arrival_time = timezone.now() + timedelta(minutes=estimated_time)
            
            hospital_data = {
                'id': hospital.id,
                'name': hospital.name,
                'address': hospital.address,
                'phone_number': hospital.phone_number,
                'emergency_phone': hospital.emergency_phone,
                'hospital_type': hospital.hospital_type,
                'has_emergency_department': hospital.has_emergency_department,
                'has_trauma_center': hospital.has_trauma_center,
                'trauma_level': hospital.trauma_level,
                'current_wait_time': hospital.current_wait_time,
                'accepts_ambulances': hospital.accepts_ambulances,
                'is_on_diversion': hospital.is_on_diversion,
                'bed_capacity': hospital.bed_capacity,
                'icu_beds': hospital.icu_beds,
                'location': {
                    'latitude': float(hospital.latitude) if hospital.latitude else None,
                    'longitude': float(hospital.longitude) if hospital.longitude else None
                },
                'distance': {
                    'km': round(distance_km, 1),
                    'miles': round(distance_km * 0.621371, 1),
                    'text': f"{distance_km:.1f} km"
                },
                'travel_time': {
                    'minutes': estimated_time,
                    'text': f"{estimated_time} min",
                    'with_traffic': f"{estimated_time}-{estimated_time + 5} min"
                },
                'arrival_time': {
                    'timestamp': arrival_time.isoformat(),
                    'text': arrival_time.strftime('%I:%M %p')
                },
                'route_info': {
                    'google_maps_url': f"https://www.google.com/maps/dir/{lat},{lng}/{hospital.latitude},{hospital.longitude}",
                    'navigation_url': f"https://www.google.com/maps/dir/?api=1&origin={lat},{lng}&destination={hospital.latitude},{hospital.longitude}&travelmode=driving&dir_action=navigate",
                    'share_url': f"https://maps.google.com/?q={hospital.latitude},{hospital.longitude}",
                    'embed_url': f"https://www.google.com/maps/embed/v1/directions?key=YOUR_API_KEY&origin={lat},{lng}&destination={hospital.latitude},{hospital.longitude}&mode=driving"
                },
                'emergency_info': {
                    'priority_score': self.calculate_priority_score(hospital, distance_km, estimated_time),
                    'recommended': distance_km < 5 and hospital.has_emergency_department and not hospital.is_on_diversion,
                    'status': 'available' if hospital.accepts_ambulances and not hospital.is_on_diversion else 'limited'
                }
            }
            enhanced_hospitals.append(hospital_data)
        
        # Sort by priority score (best options first)
        enhanced_hospitals.sort(key=lambda x: x['emergency_info']['priority_score'], reverse=True)
        
        return Response({
            'hospitals': enhanced_hospitals,
            'search_center': {'latitude': lat, 'longitude': lng},
            'search_radius_km': radius,
            'total_found': len(enhanced_hospitals),
            'timestamp': timezone.now().isoformat()
        })
    
    def calculate_priority_score(self, hospital, distance_km, travel_time_minutes):
        """Calculate priority score for hospital selection"""
        score = 100  # Base score
        
        # Distance factor (closer is better)
        if distance_km < 2:
            score += 20
        elif distance_km < 5:
            score += 10
        elif distance_km > 10:
            score -= 20
        
        # Travel time factor
        if travel_time_minutes < 10:
            score += 15
        elif travel_time_minutes > 20:
            score -= 15
        
        # Hospital capabilities
        if hospital.has_trauma_center:
            score += 25
        if hospital.has_emergency_department:
            score += 15
        if hospital.trauma_level in ['I', 'II']:
            score += 20
        
        # Current status
        if hospital.is_on_diversion:
            score -= 30
        if not hospital.accepts_ambulances:
            score -= 25
        if hospital.current_wait_time > 60:  # More than 1 hour wait
            score -= 10
        
        return max(0, score)

class CalculateEmergencyRouteView(APIView):
    """Calculate optimized route for emergency response"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        data = request.data
        
        # Extract locations
        ambulance_location = data.get('ambulance_location')
        emergency_location = data.get('emergency_location')
        hospital_location = data.get('hospital_location')
        
        if not ambulance_location or not emergency_location:
            return Response(
                {'error': 'Ambulance and emergency locations are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Calculate route to emergency
            to_emergency = self.calculate_route_segment(
                ambulance_location, 
                emergency_location,
                'to_emergency'
            )
            
            # Calculate route to hospital if provided
            to_hospital = None
            if hospital_location:
                to_hospital = self.calculate_route_segment(
                    emergency_location,
                    hospital_location,
                    'to_hospital'
                )
            
            # Calculate total time and distance
            total_time = to_emergency['duration']['minutes']
            total_distance = to_emergency['distance']['km']
            
            if to_hospital:
                total_time += to_hospital['duration']['minutes']
                total_distance += to_hospital['distance']['km']
            
            # Calculate arrival times
            now = timezone.now()
            emergency_arrival = now + timedelta(minutes=to_emergency['duration']['minutes'])
            hospital_arrival = None
            if to_hospital:
                hospital_arrival = emergency_arrival + timedelta(minutes=to_hospital['duration']['minutes'])
            
            route_info = {
                'route_id': f"route_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
                'to_emergency': to_emergency,
                'to_hospital': to_hospital,
                'total_time': {
                    'minutes': total_time,
                    'text': f"{total_time} min"
                },
                'total_distance': {
                    'km': round(total_distance, 1),
                    'text': f"{total_distance:.1f} km"
                },
                'arrival_times': {
                    'emergency_scene': {
                        'timestamp': emergency_arrival.isoformat(),
                        'text': emergency_arrival.strftime('%I:%M %p')
                    },
                    'hospital': {
                        'timestamp': hospital_arrival.isoformat() if hospital_arrival else None,
                        'text': hospital_arrival.strftime('%I:%M %p') if hospital_arrival else None
                    }
                },
                'route_options': {
                    'fastest': True,
                    'avoid_tolls': False,
                    'avoid_highways': False
                },
                'traffic_conditions': 'moderate',  # This would come from real traffic data
                'calculated_at': now.isoformat()
            }
            
            return Response(route_info)
            
        except Exception as e:
            return Response(
                {'error': f'Route calculation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def calculate_route_segment(self, origin, destination, segment_type):
        """Calculate a single route segment"""
        # Calculate distance using Haversine formula
        distance_km = self.calculate_distance(
            origin['latitude'], origin['longitude'],
            destination['latitude'], destination['longitude']
        )
        
        # Estimate travel time based on distance and road conditions
        # This is a simplified calculation - in production, use Google Maps API
        base_speed_kmh = 50  # Average speed in km/h
        if segment_type == 'to_emergency':
            base_speed_kmh = 60  # Emergency vehicles can go faster
        
        travel_time_hours = distance_km / base_speed_kmh
        travel_time_minutes = int(travel_time_hours * 60)
        
        # Add traffic delay
        traffic_delay = max(1, int(travel_time_minutes * 0.2))  # 20% delay
        total_time = travel_time_minutes + traffic_delay
        
        return {
            'origin': origin,
            'destination': destination,
            'distance': {
                'km': round(distance_km, 1),
                'miles': round(distance_km * 0.621371, 1),
                'text': f"{distance_km:.1f} km"
            },
            'duration': {
                'minutes': total_time,
                'text': f"{total_time} min",
                'base_time': travel_time_minutes,
                'traffic_delay': traffic_delay
            },
            'google_maps_url': f"https://www.google.com/maps/dir/{origin['latitude']},{origin['longitude']}/{destination['latitude']},{destination['longitude']}",
            'navigation_url': f"https://www.google.com/maps/dir/?api=1&origin={origin['latitude']},{origin['longitude']}&destination={destination['latitude']},{destination['longitude']}&travelmode=driving&dir_action=navigate"
        }
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula"""
        import math
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Earth's radius in kilometers
        
        return c * r

class NavigationInstructionsView(APIView):
    """Get turn-by-turn navigation instructions for emergency"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        emergency = get_object_or_404(EmergencyRequest, pk=pk)
        
        # Mock navigation instructions - in production, use Google Maps Directions API
        instructions = [
            {
                'step': 1,
                'instruction': 'Head north on Main St toward 1st Ave',
                'distance': '0.2 km',
                'duration': '1 min',
                'maneuver': 'straight',
                'icon': '↑'
            },
            {
                'step': 2,
                'instruction': 'Turn right onto 1st Ave',
                'distance': '0.5 km',
                'duration': '2 min',
                'maneuver': 'turn-right',
                'icon': '↱'
            },
            {
                'step': 3,
                'instruction': 'Continue straight for 2.3 km',
                'distance': '2.3 km',
                'duration': '4 min',
                'maneuver': 'straight',
                'icon': '↑'
            },
            {
                'step': 4,
                'instruction': 'Turn left onto Emergency Location St',
                'distance': '0.1 km',
                'duration': '1 min',
                'maneuver': 'turn-left',
                'icon': '↰'
            },
            {
                'step': 5,
                'instruction': 'Arrive at destination on the right',
                'distance': '0 km',
                'duration': '0 min',
                'maneuver': 'arrive',
                'icon': '📍'
            }
        ]
        
        return Response({
            'emergency_id': emergency.request_id,
            'destination': {
                'address': emergency.location,
                'coordinates': {
                    'latitude': float(emergency.latitude) if emergency.latitude else None,
                    'longitude': float(emergency.longitude) if emergency.longitude else None
                }
            },
            'instructions': instructions,
            'total_distance': '3.1 km',
            'total_duration': '8 min',
            'traffic_conditions': 'light',
            'last_updated': timezone.now().isoformat()
        })

class RealTimeETAView(APIView):
    """Get real-time ETA updates for emergency"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        emergency = get_object_or_404(EmergencyRequest, pk=pk)
        
        # Mock real-time ETA - in production, this would track actual ambulance location
        current_time = timezone.now()
        
        # Simulate ambulance progress
        if emergency.status == 'dispatched':
            eta_minutes = 12
            status_text = 'En route to emergency location'
        elif emergency.status == 'en_route':
            eta_minutes = 8
            status_text = 'Approaching emergency location'
        elif emergency.status == 'arrived':
            eta_minutes = 0
            status_text = 'Arrived at emergency location'
        elif emergency.status == 'transporting':
            eta_minutes = 15
            status_text = 'Transporting to hospital'
        else:
            eta_minutes = 15
            status_text = 'Preparing for dispatch'
        
        arrival_time = current_time + timedelta(minutes=eta_minutes)
        
        return Response({
            'emergency_id': emergency.request_id,
            'current_status': emergency.status,
            'status_text': status_text,
            'eta': {
                'minutes': eta_minutes,
                'text': f"{eta_minutes} min" if eta_minutes > 0 else 'Arrived',
                'arrival_time': arrival_time.strftime('%I:%M %p') if eta_minutes > 0 else 'Now'
            },
            'ambulance_info': {
                'id': emergency.assigned_ambulance.ambulance_id if emergency.assigned_ambulance else 'AMB-001',
                'current_location': 'Main St & 5th Ave',
                'distance_remaining': f"{eta_minutes * 0.8:.1f} km" if eta_minutes > 0 else '0 km'
            },
            'last_updated': current_time.isoformat(),
            'next_update_in': 30  # seconds
        })

class UpdateAmbulanceLocationView(APIView):
    """Update ambulance location for real-time tracking"""
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request, ambulance_id):
        try:
            ambulance = Ambulance.objects.get(ambulance_id=ambulance_id)
        except Ambulance.DoesNotExist:
            return Response(
                {'error': 'Ambulance not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        location_name = request.data.get('location_name')
        
        if not latitude or not longitude:
            return Response(
                {'error': 'Latitude and longitude are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lat = float(latitude)
            lng = float(longitude)
        except ValueError:
            return Response(
                {'error': 'Invalid coordinates'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update ambulance location
        ambulance.update_location(lat, lng, location_name)
        
        return Response({
            'ambulance_id': ambulance.ambulance_id,
            'location': {
                'latitude': float(ambulance.current_latitude),
                'longitude': float(ambulance.current_longitude),
                'address': ambulance.current_location
            },
            'last_updated': ambulance.last_location_update.isoformat(),
            'status': ambulance.status
        })