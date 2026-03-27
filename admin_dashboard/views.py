import csv
import json
from datetime import datetime, timedelta
from io import StringIO
from django.http import HttpResponse
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

from .permissions import IsAdminUser
from .serializers import (
    AdminCreatePatientSerializer, 
    AdminCreateDoctorSerializer,
    ReportRequestSerializer
)

# Import models from other apps
User = get_user_model()

try:
    from patients.models import Patient
    PATIENTS_APP = True
except ImportError:
    PATIENTS_APP = False
    Patient = None

try:
    from doctors.models import Doctor
    DOCTORS_APP = True
except ImportError:
    DOCTORS_APP = False
    Doctor = None

try:
    from appointments.models import Appointment
    APPOINTMENTS_APP = True
except ImportError:
    APPOINTMENTS_APP = False
    Appointment = None

try:
    from prescriptions.models import Prescription
    PRESCRIPTIONS_APP = True
except ImportError:
    PRESCRIPTIONS_APP = False
    Prescription = None

try:
    from billing.models import Invoice
    BILLING_APP = True
except ImportError:
    BILLING_APP = False
    Invoice = None

try:
    from emergency.models import emergency
    EMERGENCY_APP = True
except ImportError:
    EMERGENCY_APP = False
    emergency = None

try:
    from chat.models import chat
    CHAT_APP = True
except ImportError:
    CHAT_APP = False
    chat = None

try:
    from labs.models import lab
    LAB_APP = True
except ImportError:
    LAB_APP = False
    lab = None

try:
    from medical_records.models import medical_record
    MEDICALRECORD_APP = True
except ImportError:
    MEDICALRECORD_APP = False
    medical_record = None   

try:
    from medicationManagment.models import medicationManagment
    medicationManagment_APP = True
except ImportError:
    medicationManagment_APP = False
    medicationManagment = None 

try:
    from notifications.models import notification
    NOTIFICATION_APP = True
except ImportError:
    NOTIFICATION_APP = False
    notification = None      
class AdminDashboardStatsView(APIView):
    """
    Get comprehensive dashboard statistics for admin users
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        try:
            today = timezone.now().date()
            thirty_days_ago = today - timedelta(days=30)
            
            stats = {
                'user_stats': self.get_user_stats(today, thirty_days_ago),
                'appointment_stats': self.get_appointment_stats(today, thirty_days_ago) if APPOINTMENTS_APP else {},
                'financial_stats': self.get_financial_stats(today, thirty_days_ago) if BILLING_APP else {},
                'system_stats': self.get_system_stats(),
            }
            
            return Response(stats)
            
        except Exception as e:
            return Response(
                {'error': f'Error fetching dashboard stats: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_user_stats(self, today, thirty_days_ago):
        """Get user-related statistics"""
        user_stats = {
            'total_users': User.objects.count(),
            'total_admins': User.objects.filter(role='ADMIN').count(),
            'new_users_today': User.objects.filter(date_joined__date=today).count(),
            'new_users_30_days': User.objects.filter(date_joined__gte=thirty_days_ago).count(),
        }
        
        if PATIENTS_APP:
            user_stats.update({
                'total_patients': Patient.objects.count(),
                'new_patients_today': Patient.objects.filter(created_at__date=today).count(),
                'new_patients_30_days': Patient.objects.filter(created_at__gte=thirty_days_ago).count(),
                'patient_gender_distribution': list(Patient.objects.values('gender').annotate(count=Count('id'))),
            })
        
        if DOCTORS_APP:
            user_stats.update({
                'total_doctors': Doctor.objects.count(),
                'available_doctors': Doctor.objects.filter(is_available=True).count(),
                'verified_doctors': Doctor.objects.filter(is_verified=True).count(),
                'unverified_doctors': Doctor.objects.filter(is_verified=False).count(),
                'new_doctors_today': Doctor.objects.filter(created_at__date=today).count(),
                'doctor_specialization_distribution': list(Doctor.objects.values('specialization').annotate(count=Count('id')).order_by('-count')[:10]),
            })
        
        return user_stats
    
    def get_appointment_stats(self, today, thirty_days_ago):
        """Get appointment-related statistics"""
        if not APPOINTMENTS_APP:
            return {}
            
        appointments_today = Appointment.objects.filter(appointment_date=today)
        appointments_30_days = Appointment.objects.filter(appointment_date__gte=thirty_days_ago)
        
        return {
            'appointments_today': appointments_today.count(),
            'appointments_30_days': appointments_30_days.count(),
            'appointment_status_today': list(appointments_today.values('status').annotate(count=Count('id'))),
            'appointment_status_30_days': list(appointments_30_days.values('status').annotate(count=Count('id'))),
            'busiest_doctors_today': list(
                appointments_today.values('doctor__user__first_name', 'doctor__user__last_name')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            ),
        }
    
    def get_financial_stats(self, today, thirty_days_ago):
        """Get financial statistics"""
        if not BILLING_APP:
            return {}
            
        invoices_30_days = Invoice.objects.filter(created_at__gte=thirty_days_ago)
        
        return {
            'total_revenue_30_days': invoices_30_days.aggregate(total=Sum('total_amount'))['total'] or 0,
            'paid_invoices_30_days': invoices_30_days.filter(status='paid').count(),
            'pending_invoices_30_days': invoices_30_days.filter(status='pending').count(),
            'average_invoice_amount': invoices_30_days.aggregate(avg=Avg('total_amount'))['avg'] or 0,
        }
    
    def get_system_stats(self):
        """Get system-level statistics"""
        return {
            'server_time': timezone.now().isoformat(),
            'debug_mode': getattr(settings, 'DEBUG', False),
            'api_version': '1.0.0',
        }


class AdminRecentActivitiesView(APIView):
    """
    Get recent system activities for admin dashboard
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        try:
            activities = []
            
            # Recent user registrations
            recent_users = User.objects.order_by('-date_joined')[:10]
            for user in recent_users:
                activities.append({
                    'id': user.id,
                    'action': f'{user.get_role_display()} registered',
                    'user': f"{user.first_name} {user.last_name}",
                    'email': user.email,
                    'role': user.role,
                    'time': self.format_time_ago(user.date_joined),
                    'type': 'user_registration',
                })
            
            # Recent appointments if available
            if APPOINTMENTS_APP:
                recent_appointments = Appointment.objects.select_related(
                    'patient__user', 'doctor__user'
                ).order_by('-created_at')[:10]
                
                for appointment in recent_appointments:
                    activities.append({
                        'id': appointment.id,
                        'action': f'Appointment {appointment.get_status_display().lower()}',
                        'user': f"{appointment.patient.user.first_name} with Dr. {appointment.doctor.user.last_name}",
                        'time': self.format_time_ago(appointment.created_at),
                        'type': 'appointment',
                        'status': appointment.status,
                        'date': appointment.appointment_date,
                    })
            
            # Sort by time (most recent first)
            activities.sort(key=lambda x: x['time'], reverse=True)
            
            return Response(activities[:20])  # Return top 20 most recent
            
        except Exception as e:
            return Response(
                {'error': f'Error fetching recent activities: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def format_time_ago(self, dt):
        """Format datetime as time ago string"""
        now = timezone.now()
        diff = now - dt
        
        if diff.days > 365:
            years = diff.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"


class AdminPendingActionsView(APIView):
    """
    Get pending actions requiring admin attention
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        try:
            pending_actions = []
            
            # Unverified doctors
            if DOCTORS_APP:
                unverified_doctors = Doctor.objects.filter(is_verified=False).select_related('user')
                for doctor in unverified_doctors:
                    days_pending = (timezone.now() - doctor.created_at).days
                    pending_actions.append({
                        'id': doctor.id,
                        'type': 'DOCTOR_VERIFICATION',
                        'title': 'Doctor Verification Required',
                        'description': f"Dr. {doctor.user.first_name} {doctor.user.last_name} is awaiting verification",
                        'user': f"Dr. {doctor.user.first_name} {doctor.user.last_name}",
                        'specialization': doctor.specialization,
                        'qualifications': doctor.qualifications,
                        'days_pending': days_pending,
                        'priority': 'HIGH' if days_pending > 3 else 'MEDIUM',
                        'created_at': doctor.created_at.isoformat(),
                        'action_url': f'/admin/doctors/doctor/{doctor.id}/change/',
                    })
            
            # Pending appointments needing attention
            if APPOINTMENTS_APP:
                problematic_appointments = Appointment.objects.filter(
                    Q(status='pending') | Q(status='cancelled')
                ).select_related('patient__user', 'doctor__user')[:10]
                
                for appointment in problematic_appointments:
                    pending_actions.append({
                        'id': appointment.id,
                        'type': 'APPOINTMENT_REVIEW',
                        'title': f'Appointment {appointment.get_status_display()}',
                        'description': f"Appointment for {appointment.patient.user.first_name} with Dr. {appointment.doctor.user.last_name}",
                        'user': appointment.patient.user.first_name,
                        'doctor': f"Dr. {appointment.doctor.user.last_name}",
                        'date': appointment.appointment_date,
                        'status': appointment.status,
                        'priority': 'HIGH' if appointment.status == 'cancelled' else 'MEDIUM',
                        'created_at': appointment.created_at.isoformat(),
                        'action_url': f'/admin/appointments/appointment/{appointment.id}/change/',
                    })
            
            # Sort by priority and recency
            priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
            pending_actions.sort(key=lambda x: (
                priority_order.get(x['priority'], 3),
                -datetime.fromisoformat(x['created_at']).timestamp()
            ))
            
            return Response(pending_actions)
            
        except Exception as e:
            return Response(
                {'error': f'Error fetching pending actions: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminAnalyticsView(APIView):
    """
    Get system analytics and performance metrics
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        try:
            today = timezone.now().date()
            last_7_days = today - timedelta(days=7)
            last_30_days = today - timedelta(days=30)
            
            analytics = {
                'periods': {
                    'today': today.isoformat(),
                    'last_7_days': last_7_days.isoformat(),
                    'last_30_days': last_30_days.isoformat(),
                },
                'user_engagement': self.get_user_engagement(today, last_7_days, last_30_days),
                'appointment_analytics': self.get_appointment_analytics(today, last_7_days, last_30_days) if APPOINTMENTS_APP else {},
                'system_performance': self.get_system_performance(),
            }
            
            return Response(analytics)
            
        except Exception as e:
            return Response(
                {'error': f'Error fetching analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_user_engagement(self, today, last_7_days, last_30_days):
        """Calculate user engagement metrics"""
        users_last_24h = User.objects.filter(last_login__gte=timezone.now() - timedelta(hours=24)).count()
        users_last_7d = User.objects.filter(last_login__gte=last_7_days).count()
        users_last_30d = User.objects.filter(last_login__gte=last_30_days).count()
        total_users = User.objects.count()
        
        return {
            'active_users_24h': users_last_24h,
            'active_users_7d': users_last_7d,
            'active_users_30d': users_last_30d,
            'total_users': total_users,
            'engagement_rate_24h': round((users_last_24h / total_users * 100), 2) if total_users > 0 else 0,
            'engagement_rate_7d': round((users_last_7d / total_users * 100), 2) if total_users > 0 else 0,
        }
    
    def get_appointment_analytics(self, today, last_7_days, last_30_days):
        """Calculate appointment analytics"""
        if not APPOINTMENTS_APP:
            return {}
            
        appointments_30d = Appointment.objects.filter(appointment_date__gte=last_30_days)
        completed_appointments = appointments_30d.filter(status='completed').count()
        cancelled_appointments = appointments_30d.filter(status='cancelled').count()
        total_appointments = appointments_30d.count()
        
        return {
            'appointments_30d': total_appointments,
            'completion_rate': round((completed_appointments / total_appointments * 100), 2) if total_appointments > 0 else 0,
            'cancellation_rate': round((cancelled_appointments / total_appointments * 100), 2) if total_appointments > 0 else 0,
            'average_daily_appointments': round(total_appointments / 30, 2),
        }
    
    def get_system_performance(self):
        """Get system performance metrics"""
        # These would typically come from monitoring systems
        # For now, returning mock/placeholder data
        return {
            'server_uptime': '99.9%',
            'api_response_time': '120ms',
            'database_latency': '15ms',
            'cache_hit_rate': '92%',
            'active_connections': 45,
        }


class AdminCreatePatientView(CreateAPIView):
    """
    Admin endpoint to create new patients
    """
    serializer_class = AdminCreatePatientSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    parser_classes = [JSONParser]
    renderer_classes = [JSONRenderer]
    
    def log_admin_action(self, user, action):
        """Log admin actions for audit trail"""
        # You can implement proper logging here
        # For now, just print to console
        print(f"ADMIN ACTION: {user.username} - {action} at {timezone.now()}")
    
    def create(self, request, *args, **kwargs):
        try:
            print("=" * 50)
            print("ADMIN CREATE PATIENT - DEBUG")
            print(f"Request data: {request.data}")
            print(f"Request user: {request.user}")
            print(f"User is authenticated: {request.user.is_authenticated}")
            print(f"User role: {getattr(request.user, 'role', 'No role')}")
            print("=" * 50)
            
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                print("❌ SERIALIZER VALIDATION FAILED:")
                print(f"Errors: {serializer.errors}")
                return Response({
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print("✅ SERIALIZER VALIDATION PASSED")
            
            # Create patient
            patient = serializer.save()
            print(f"✅ PATIENT CREATED: {patient}")
            
            # Log the action (you might want to implement an audit log)
            self.log_admin_action(request.user, f"Created patient: {patient.user.email}")
            
            return Response({
                'status': 'success',
                'message': 'Patient created successfully',
                'patient_id': patient.id,
                'user_id': patient.user.id,
                'email': patient.user.email,
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"❌ EXCEPTION OCCURRED: {str(e)}")
            print(f"Exception type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            
            return Response({
                'status': 'error',
                'message': str(e),
                'errors': {}
            }, status=status.HTTP_400_BAD_REQUEST)


class AdminCreateDoctorView(CreateAPIView):
    """
    Admin endpoint to create new doctors
    """
    serializer_class = AdminCreateDoctorSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    parser_classes = [JSONParser]
    renderer_classes = [JSONRenderer]
    
    def log_admin_action(self, user, action):
        """Log admin actions for audit trail"""
        # You can implement proper logging here
        # For now, just print to console
        print(f"ADMIN ACTION: {user.username} - {action} at {timezone.now()}")
    
    def create(self, request, *args, **kwargs):
        try:
            print("=" * 50)
            print("ADMIN CREATE DOCTOR - DEBUG")
            print(f"Request data: {request.data}")
            print(f"Request user: {request.user}")
            print(f"User is authenticated: {request.user.is_authenticated}")
            print(f"User role: {getattr(request.user, 'role', 'No role')}")
            print("=" * 50)
            
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                print("❌ SERIALIZER VALIDATION FAILED:")
                print(f"Errors: {serializer.errors}")
                return Response({
                    'status': 'error',
                    'message': 'Validation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            print("✅ SERIALIZER VALIDATION PASSED")
            
            # Create doctor
            doctor = serializer.save()
            print(f"✅ DOCTOR CREATED: {doctor}")
            
            # Log the action
            self.log_admin_action(request.user, f"Created doctor: {doctor.user.email}")
            
            return Response({
                'status': 'success',
                'message': 'Doctor created successfully',
                'doctor_id': doctor.id,
                'user_id': doctor.user.id,
                'email': doctor.user.email,
                'specialization': doctor.specialization.name if doctor.specialization else None,
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"❌ EXCEPTION OCCURRED: {str(e)}")
            print(f"Exception type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            
            return Response({
                'status': 'error',
                'message': str(e),
                'errors': {}
            }, status=status.HTTP_400_BAD_REQUEST)


class SystemStatusView(APIView):
    """
    Check system health and status
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        try:
            # Check database connection
            from django.db import connection
            try:
                connection.ensure_connection()
                db_status = 'connected'
                db_latency = self.test_db_latency()
            except Exception as e:
                db_status = f'error: {str(e)}'
                db_latency = None
            
            # Check cache
            from django.core.cache import cache
            try:
                cache.set('health_check', 'ok', 5)
                cache_ok = cache.get('health_check') == 'ok'
                cache_status = 'ok' if cache_ok else 'error'
            except Exception as e:
                cache_status = f'error: {str(e)}'
            
            # Check storage
            from django.conf import settings
            import os
            try:
                if hasattr(settings, 'MEDIA_ROOT'):
                    media_path = settings.MEDIA_ROOT
                    media_writable = os.access(media_path, os.W_OK) if os.path.exists(media_path) else True
                else:
                    media_writable = True
                storage_status = 'writable' if media_writable else 'read_only'
            except Exception as e:
                storage_status = f'error: {str(e)}'
            
            # Get recent errors from logs (simplified)
            recent_errors = self.get_recent_errors()
            
            return Response({
                'status': 'operational',
                'timestamp': timezone.now().isoformat(),
                'components': {
                    'database': {
                        'status': db_status,
                        'latency_ms': db_latency,
                        'engine': connection.vendor,
                    },
                    'cache': {
                        'status': cache_status,
                        'backend': getattr(settings, 'CACHES', {}).get('default', {}).get('BACKEND', 'unknown'),
                    },
                    'storage': {
                        'status': storage_status,
                        'media_root': getattr(settings, 'MEDIA_ROOT', 'not_set'),
                    },
                },
                'system_info': {
                    'debug_mode': settings.DEBUG,
                    'timezone': settings.TIME_ZONE,
                    'language_code': settings.LANGUAGE_CODE,
                    'installed_apps_count': len(settings.INSTALLED_APPS),
                },
                'recent_errors': recent_errors,
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error checking system status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def test_db_latency(self):
        """Test database query latency"""
        import time
        from django.db import connection
        
        start_time = time.time()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except:
            return None
        
        return round((time.time() - start_time) * 1000, 2)  # Convert to ms
    
    def get_recent_errors(self):
        """Get recent system errors (placeholder - implement based on your logging)"""
        # In production, you would query your error logging system
        return []


class GenerateReportView(APIView):
    """
    Generate and download reports in various formats
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def post(self, request):
        serializer = ReportRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        report_type = serializer.validated_data['report_type']
        start_date = serializer.validated_data.get('start_date')
        end_date = serializer.validated_data.get('end_date')
        report_format = serializer.validated_data['format']
        
        try:
            # Generate report data based on type
            report_data = self.generate_report_data(report_type, start_date, end_date)
            
            # Format response based on requested format
            if report_format == 'json':
                return Response(report_data)
            elif report_format == 'csv':
                return self.generate_csv_response(report_data, report_type)
            elif report_format == 'pdf':
                return self.generate_pdf_response(report_data, report_type)
            else:
                return Response(
                    {'error': 'Unsupported format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': f'Error generating report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def generate_report_data(self, report_type, start_date, end_date):
        """Generate report data based on type"""
        if report_type == 'patients_summary' and PATIENTS_APP:
            return self.generate_patients_summary(start_date, end_date)
        elif report_type == 'doctors_summary' and DOCTORS_APP:
            return self.generate_doctors_summary(start_date, end_date)
        elif report_type == 'appointments_summary' and APPOINTMENTS_APP:
            return self.generate_appointments_summary(start_date, end_date)
        elif report_type == 'financial_summary' and BILLING_APP:
            return self.generate_financial_summary(start_date, end_date)
        else:
            raise ValueError(f"Unsupported report type: {report_type}")
    
    def generate_patients_summary(self, start_date, end_date):
        """Generate patients summary report"""
        queryset = Patient.objects.all()
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        patients = queryset.select_related('user').values(
            'id', 'user__first_name', 'user__last_name', 'user__email',
            'age', 'gender', 'blood_group', 'created_at'
        )
        
        return {
            'report_type': 'patients_summary',
            'generated_at': timezone.now().isoformat(),
            'period': {
                'start_date': start_date.isoformat() if start_date else 'all_time',
                'end_date': end_date.isoformat() if end_date else 'all_time',
            },
            'total_patients': patients.count(),
            'patients': list(patients),
            'summary': {
                'gender_distribution': list(Patient.objects.values('gender').annotate(count=Count('id'))),
                'age_groups': self.get_age_groups_distribution(),
            }
        }
    
    def generate_doctors_summary(self, start_date, end_date):
        """Generate doctors summary report"""
        queryset = Doctor.objects.all()
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        doctors = queryset.select_related('user').values(
            'id', 'user__first_name', 'user__last_name', 'user__email',
            'specialization', 'department', 'is_available', 'is_verified',
            'experience_years', 'consultation_fee', 'created_at'
        )
        
        return {
            'report_type': 'doctors_summary',
            'generated_at': timezone.now().isoformat(),
            'period': {
                'start_date': start_date.isoformat() if start_date else 'all_time',
                'end_date': end_date.isoformat() if end_date else 'all_time',
            },
            'total_doctors': doctors.count(),
            'doctors': list(doctors),
            'summary': {
                'specialization_distribution': list(Doctor.objects.values('specialization').annotate(count=Count('id')).order_by('-count')),
                'availability': {
                    'available': Doctor.objects.filter(is_available=True).count(),
                    'unavailable': Doctor.objects.filter(is_available=False).count(),
                },
                'verification': {
                    'verified': Doctor.objects.filter(is_verified=True).count(),
                    'unverified': Doctor.objects.filter(is_verified=False).count(),
                },
            }
        }
    
    def generate_appointments_summary(self, start_date, end_date):
        """Generate appointments summary report"""
        if not APPOINTMENTS_APP:
            return {'error': 'Appointments app not available'}
        
        queryset = Appointment.objects.all()
        if start_date:
            queryset = queryset.filter(appointment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(appointment_date__lte=end_date)
        
        appointments = queryset.select_related(
            'patient__user', 'doctor__user'
        ).values(
            'id', 'patient__user__first_name', 'patient__user__last_name',
            'doctor__user__first_name', 'doctor__user__last_name',
            'appointment_date', 'appointment_time', 'status', 'created_at'
        )
        
        return {
            'report_type': 'appointments_summary',
            'generated_at': timezone.now().isoformat(),
            'period': {
                'start_date': start_date.isoformat() if start_date else 'all_time',
                'end_date': end_date.isoformat() if end_date else 'all_time',
            },
            'total_appointments': appointments.count(),
            'appointments': list(appointments),
            'summary': {
                'status_distribution': list(Appointment.objects.values('status').annotate(count=Count('id'))),
                'daily_average': self.get_daily_appointment_average(start_date, end_date),
            }
        }
    
    def generate_financial_summary(self, start_date, end_date):
        """Generate financial summary report"""
        if not BILLING_APP:
            return {'error': 'Billing app not available'}
        
        queryset = Invoice.objects.all()
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        invoices = queryset.values(
            'id', 'invoice_number', 'patient__user__first_name', 'patient__user__last_name',
            'total_amount', 'status', 'created_at', 'paid_at'
        )
        
        total_revenue = queryset.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or 0
        
        return {
            'report_type': 'financial_summary',
            'generated_at': timezone.now().isoformat(),
            'period': {
                'start_date': start_date.isoformat() if start_date else 'all_time',
                'end_date': end_date.isoformat() if end_date else 'all_time',
            },
            'total_invoices': invoices.count(),
            'total_revenue': float(total_revenue),
            'invoices': list(invoices),
            'summary': {
                'status_distribution': list(Invoice.objects.values('status').annotate(count=Count('id'))),
                'revenue_by_month': self.get_revenue_by_month(start_date, end_date),
            }
        }
    
    def get_age_groups_distribution(self):
        """Helper to get age groups distribution"""
        if not PATIENTS_APP:
            return []
        
        age_groups = {
            '0-17': Patient.objects.filter(age__lte=17).count(),
            '18-30': Patient.objects.filter(age__range=(18, 30)).count(),
            '31-45': Patient.objects.filter(age__range=(31, 45)).count(),
            '46-60': Patient.objects.filter(age__range=(46, 60)).count(),
            '61+': Patient.objects.filter(age__gte=61).count(),
        }
        
        return [{'age_group': k, 'count': v} for k, v in age_groups.items()]
    
    def get_daily_appointment_average(self, start_date, end_date):
        """Calculate daily appointment average"""
        if not APPOINTMENTS_APP:
            return 0
        
        if start_date and end_date:
            days = (end_date - start_date).days + 1
            if days > 0:
                total = Appointment.objects.filter(
                    appointment_date__range=[start_date, end_date]
                ).count()
                return round(total / days, 2)
        return 0
    
    def get_revenue_by_month(self, start_date, end_date):
        """Get revenue grouped by month"""
        if not BILLING_APP:
            return []
        
        from django.db.models.functions import TruncMonth
        
        revenue_by_month = Invoice.objects.filter(
            status='paid',
            created_at__date__gte=start_date if start_date else datetime.min.date(),
            created_at__date__lte=end_date if end_date else datetime.max.date()
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total=Sum('total_amount')
        ).order_by('month')
        
        return list(revenue_by_month)
    
    def generate_csv_response(self, report_data, report_type):
        """Generate CSV response from report data"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_{timezone.now().date()}.csv"'
        
        writer = csv.writer(response)
        
        # Write header based on report type
        if 'patients' in report_type and 'patients' in report_data:
            writer.writerow(['ID', 'First Name', 'Last Name', 'Email', 'Age', 'Gender', 'Blood Group', 'Created At'])
            for patient in report_data['patients']:
                writer.writerow([
                    patient['id'],
                    patient['user__first_name'],
                    patient['user__last_name'],
                    patient['user__email'],
                    patient['age'],
                    patient['gender'],
                    patient['blood_group'],
                    patient['created_at'],
                ])
        
        elif 'doctors' in report_type and 'doctors' in report_data:
            writer.writerow(['ID', 'First Name', 'Last Name', 'Email', 'Specialization', 'Department', 'Available', 'Verified', 'Experience', 'Fee'])
            for doctor in report_data['doctors']:
                writer.writerow([
                    doctor['id'],
                    doctor['user__first_name'],
                    doctor['user__last_name'],
                    doctor['user__email'],
                    doctor['specialization'],
                    doctor['department'],
                    'Yes' if doctor['is_available'] else 'No',
                    'Yes' if doctor['is_verified'] else 'No',
                    doctor['experience_years'],
                    doctor['consultation_fee'],
                ])
        
        elif 'appointments' in report_type and 'appointments' in report_data:
            writer.writerow(['ID', 'Patient Name', 'Doctor Name', 'Date', 'Time', 'Status', 'Created At'])
            for appointment in report_data['appointments']:
                writer.writerow([
                    appointment['id'],
                    f"{appointment['patient__user__first_name']} {appointment['patient__user__last_name']}",
                    f"Dr. {appointment['doctor__user__first_name']} {appointment['doctor__user__last_name']}",
                    appointment['appointment_date'],
                    appointment['appointment_time'],
                    appointment['status'],
                    appointment['created_at'],
                ])
        
        elif 'financial' in report_type and 'invoices' in report_data:
            writer.writerow(['Invoice ID', 'Invoice Number', 'Patient Name', 'Amount', 'Status', 'Created At', 'Paid At'])
            for invoice in report_data['invoices']:
                writer.writerow([
                    invoice['id'],
                    invoice['invoice_number'],
                    f"{invoice['patient__user__first_name']} {invoice['patient__user__last_name']}",
                    invoice['total_amount'],
                    invoice['status'],
                    invoice['created_at'],
                    invoice['paid_at'],
                ])
        
        return response
    
    def generate_pdf_response(self, report_data, report_type):
        """Generate PDF response (placeholder - implement PDF generation)"""
        # For now, return JSON with note about PDF generation
        report_data['note'] = 'PDF generation not implemented. Returning JSON instead.'
        return Response(report_data)