from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
import csv
import json

from .models import VitalType, VitalReading, HealthAlert, PatientHealthSummary, HealthReport
from .serializers import (
    VitalTypeSerializer, VitalReadingSerializer, HealthAlertSerializer,
    PatientHealthSummarySerializer, HealthReportSerializer, HealthStatsSerializer
)
from patients.models import Patient
from doctors.models import Doctor

class VitalTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for vital types"""
    queryset = VitalType.objects.filter(is_active=True)
    serializer_class = VitalTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

class VitalReadingViewSet(viewsets.ModelViewSet):
    """ViewSet for vital readings"""
    serializer_class = VitalReadingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = VitalReading.objects.all()
        
        # Filter by patient if specified
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        # Filter by vital type
        vital_type = self.request.query_params.get('vital_type')
        if vital_type:
            queryset = queryset.filter(vital_type=vital_type)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(recorded_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(recorded_at__lte=date_to)
        
        # Filter by abnormal readings only
        abnormal_only = self.request.query_params.get('abnormal_only')
        if abnormal_only == 'true':
            queryset = queryset.filter(is_abnormal=True)
        
        return queryset.order_by('-recorded_at')
    
    def perform_create(self, serializer):
        # Set doctor from request user
        try:
            doctor_profile = Doctor.objects.get(user=self.request.user)
            serializer.save(doctor=doctor_profile)
        except Doctor.DoesNotExist:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def patient_vitals(self, request):
        """Get vitals for a specific patient"""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response({'error': 'patient_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)
        
        queryset = self.get_queryset().filter(patient=patient)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get vital trends for analysis"""
        patient_id = request.query_params.get('patient_id')
        vital_type = request.query_params.get('vital_type')
        days = int(request.query_params.get('days', 30))
        
        queryset = self.get_queryset()
        
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        if vital_type:
            queryset = queryset.filter(vital_type=vital_type)
        
        # Filter by date range
        date_from = timezone.now() - timedelta(days=days)
        queryset = queryset.filter(recorded_at__gte=date_from)
        
        # Group by date and calculate averages
        trends = {}
        for reading in queryset:
            date_key = reading.recorded_at.date().isoformat()
            if date_key not in trends:
                trends[date_key] = []
            
            # Handle different value types
            try:
                if reading.vital_type == 'blood_pressure' and '/' in reading.value:
                    systolic = float(reading.value.split('/')[0])
                    trends[date_key].append(systolic)
                else:
                    trends[date_key].append(float(reading.value))
            except (ValueError, TypeError):
                continue
        
        # Calculate daily averages
        trend_data = []
        for date_key, values in trends.items():
            if values:
                trend_data.append({
                    'date': date_key,
                    'average': sum(values) / len(values),
                    'count': len(values),
                    'min': min(values),
                    'max': max(values)
                })
        
        return Response(sorted(trend_data, key=lambda x: x['date']))

class HealthAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for health alerts"""
    serializer_class = HealthAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = HealthAlert.objects.all()
        
        # Filter by patient
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        # Filter by resolution status
        resolved = self.request.query_params.get('resolved')
        if resolved == 'true':
            queryset = queryset.filter(is_resolved=True)
        elif resolved == 'false':
            queryset = queryset.filter(is_resolved=False)
        
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark an alert as resolved"""
        alert = self.get_object()
        alert.resolve(user=request.user)
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_resolve(self, request):
        """Resolve multiple alerts"""
        alert_ids = request.data.get('alert_ids', [])
        if not alert_ids:
            return Response({'error': 'alert_ids is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        alerts = HealthAlert.objects.filter(id__in=alert_ids, is_resolved=False)
        count = 0
        for alert in alerts:
            alert.resolve(user=request.user)
            count += 1
        
        return Response({'resolved_count': count})

class PatientHealthSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for patient health summaries"""
    serializer_class = PatientHealthSummarySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PatientHealthSummary.objects.all().order_by('-last_updated')
    
    @action(detail=True, methods=['post'])
    def update_summary(self, request, pk=None):
        """Update health summary for a patient"""
        summary = self.get_object()
        summary.update_summary()
        serializer = self.get_serializer(summary)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def patient_summary(self, request):
        """Get health summary for a specific patient"""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response({'error': 'patient_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            patient = Patient.objects.get(id=patient_id)
            summary, created = PatientHealthSummary.objects.get_or_create(patient=patient)
            if created or summary.last_updated < timezone.now() - timedelta(hours=1):
                summary.update_summary()
            
            serializer = self.get_serializer(summary)
            return Response(serializer.data)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

class HealthReportViewSet(viewsets.ModelViewSet):
    """ViewSet for health reports"""
    serializer_class = HealthReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return HealthReport.objects.all().order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generate_patient_report(self, request):
        """Generate a comprehensive report for a patient"""
        patient_id = request.data.get('patient_id')
        date_from = request.data.get('date_from')
        date_to = request.data.get('date_to')
        
        if not all([patient_id, date_from, date_to]):
            return Response({
                'error': 'patient_id, date_from, and date_to are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Collect report data
        vitals = VitalReading.objects.filter(
            patient=patient,
            recorded_at__range=[date_from, date_to]
        ).order_by('-recorded_at')
        
        alerts = HealthAlert.objects.filter(
            patient=patient,
            created_at__range=[date_from, date_to]
        ).order_by('-created_at')
        
        # Generate report data
        report_data = {
            'patient_info': {
                'name': f"{patient.user.first_name} {patient.user.last_name}",
                'email': patient.user.email,
                'phone': getattr(patient, 'phone', ''),
                'date_of_birth': getattr(patient, 'date_of_birth', None),
            },
            'summary': {
                'total_readings': vitals.count(),
                'abnormal_readings': vitals.filter(is_abnormal=True).count(),
                'total_alerts': alerts.count(),
                'resolved_alerts': alerts.filter(is_resolved=True).count(),
            },
            'vitals': VitalReadingSerializer(vitals, many=True).data,
            'alerts': HealthAlertSerializer(alerts, many=True).data,
            'vital_trends': self._calculate_vital_trends(vitals),
        }
        
        # Create report record
        report = HealthReport.objects.create(
            title=f"Health Report - {patient.user.first_name} {patient.user.last_name}",
            report_type='patient_summary',
            patient=patient,
            generated_by=request.user,
            date_from=date_from,
            date_to=date_to,
            data=report_data,
            is_shared_with_admin=request.data.get('share_with_admin', False)
        )
        
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def system_stats(self, request):
        """Get system-wide health statistics"""
        # Calculate date ranges
        now = timezone.now()
        today = now.date()
        thirty_days_ago = now - timedelta(days=30)
        
        # Basic counts
        total_patients = Patient.objects.count()
        total_readings = VitalReading.objects.count()
        total_alerts = HealthAlert.objects.count()
        active_alerts = HealthAlert.objects.filter(is_resolved=False).count()
        abnormal_readings = VitalReading.objects.filter(is_abnormal=True).count()
        
        # Today's activity
        readings_today = VitalReading.objects.filter(recorded_at__date=today).count()
        alerts_today = HealthAlert.objects.filter(created_at__date=today).count()
        
        # Risk distribution
        risk_distribution = PatientHealthSummary.objects.values('risk_level').annotate(
            count=Count('id')
        ).order_by('risk_level')
        risk_dist_dict = {item['risk_level']: item['count'] for item in risk_distribution}
        
        # Vital type distribution
        vital_distribution = VitalReading.objects.filter(
            recorded_at__gte=thirty_days_ago
        ).values('vital_type').annotate(
            count=Count('id')
        ).order_by('-count')
        vital_dist_dict = {item['vital_type']: item['count'] for item in vital_distribution}
        
        # Recent data
        recent_readings = VitalReading.objects.order_by('-recorded_at')[:10]
        recent_alerts = HealthAlert.objects.filter(is_resolved=False).order_by('-created_at')[:10]
        
        stats_data = {
            'total_patients': total_patients,
            'total_readings': total_readings,
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'abnormal_readings': abnormal_readings,
            'readings_today': readings_today,
            'alerts_today': alerts_today,
            'risk_distribution': risk_dist_dict,
            'vital_type_distribution': vital_dist_dict,
            'recent_readings': VitalReadingSerializer(recent_readings, many=True).data,
            'recent_alerts': HealthAlertSerializer(recent_alerts, many=True).data,
        }
        
        serializer = HealthStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def export_csv(self, request, pk=None):
        """Export report data as CSV"""
        report = self.get_object()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{report.title}.csv"'
        
        writer = csv.writer(response)
        
        if report.report_type == 'patient_summary':
            # Write patient summary CSV
            writer.writerow(['Patient Health Report'])
            writer.writerow(['Generated:', report.created_at.strftime('%Y-%m-%d %H:%M')])
            writer.writerow(['Period:', f"{report.date_from} to {report.date_to}"])
            writer.writerow([])
            
            # Patient info
            patient_info = report.data.get('patient_info', {})
            writer.writerow(['Patient Information'])
            for key, value in patient_info.items():
                writer.writerow([key.replace('_', ' ').title(), value])
            writer.writerow([])
            
            # Summary
            summary = report.data.get('summary', {})
            writer.writerow(['Summary'])
            for key, value in summary.items():
                writer.writerow([key.replace('_', ' ').title(), value])
            writer.writerow([])
            
            # Vitals
            vitals = report.data.get('vitals', [])
            if vitals:
                writer.writerow(['Vital Readings'])
                writer.writerow(['Date', 'Type', 'Value', 'Unit', 'Status', 'Notes'])
                for vital in vitals:
                    writer.writerow([
                        vital.get('recorded_at', ''),
                        vital.get('vital_type_display', ''),
                        vital.get('value', ''),
                        vital.get('unit', ''),
                        'Abnormal' if vital.get('is_abnormal') else 'Normal',
                        vital.get('notes', '')
                    ])
        
        return response
    
    def _calculate_vital_trends(self, vitals):
        """Calculate trends for different vital types"""
        trends = {}
        
        for vital_type in ['blood_pressure', 'heart_rate', 'temperature', 'oxygen_saturation']:
            type_vitals = vitals.filter(vital_type=vital_type).order_by('recorded_at')
            
            if type_vitals.count() >= 2:
                values = []
                for vital in type_vitals:
                    try:
                        if vital_type == 'blood_pressure' and '/' in vital.value:
                            values.append(float(vital.value.split('/')[0]))
                        else:
                            values.append(float(vital.value))
                    except (ValueError, TypeError):
                        continue
                
                if len(values) >= 2:
                    # Simple trend calculation
                    recent_avg = sum(values[-3:]) / len(values[-3:]) if len(values) >= 3 else values[-1]
                    older_avg = sum(values[:3]) / len(values[:3]) if len(values) >= 3 else values[0]
                    
                    if recent_avg > older_avg * 1.1:
                        trend = 'increasing'
                    elif recent_avg < older_avg * 0.9:
                        trend = 'decreasing'
                    else:
                        trend = 'stable'
                    
                    trends[vital_type] = {
                        'trend': trend,
                        'recent_average': recent_avg,
                        'older_average': older_avg,
                        'total_readings': len(values)
                    }
        
        return trends