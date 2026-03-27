from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Q, Count, Avg, F  
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Appointment, AppointmentSlot
from .serializers import *

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'

# admin views
class AdminAppointmentListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    serializer_class = AppointmentSerializer
    queryset = Appointment.objects.all()
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('patient__user', 'doctor__user')
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status__iexact=status_filter)
        
        # Date filters
        date_filter = self.request.query_params.get('date')
        if date_filter:
            queryset = queryset.filter(appointment_date=date_filter)
        
        return queryset.order_by('-created_at')

class AdminAppointmentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get(self, request, pk):
        try:
            appointment = Appointment.objects.select_related(
                'patient__user', 'doctor__user'
            ).get(pk=pk)
            serializer = AppointmentSerializer(appointment)
            return Response(serializer.data)
        except Appointment.DoesNotExist:
            return Response(
                {'error': 'Appointment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class AppointmentStatisticsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        try:
            today = timezone.now().date()
            
            total = Appointment.objects.count()
            pending = Appointment.objects.filter(status__iexact='pending').count()
            confirmed = Appointment.objects.filter(status__iexact='confirmed').count()
            completed = Appointment.objects.filter(status__iexact='completed').count()
            cancelled = Appointment.objects.filter(status__iexact='cancelled').count()
            
            today_count = Appointment.objects.filter(
                appointment_date=today,
                status__in=['confirmed', 'pending']
            ).count()
            
            upcoming_count = Appointment.objects.filter(
                appointment_date__gt=today,
                status__in=['confirmed', 'pending']
            ).count()
            
            return Response({
                'total': total,
                'pending': pending,
                'confirmed': confirmed,
                'completed': completed,
                'cancelled': cancelled,
                'today': today_count,
                'upcoming': upcoming_count,
                'source': 'backend'
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CancelAppointmentView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def post(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk)
            cancellation_reason = request.data.get('cancellation_reason', '')
            
            appointment.status = 'cancelled'
            appointment.cancellation_reason = cancellation_reason
            appointment.cancelled_at = timezone.now()
            appointment.save()
            
            serializer = AppointmentSerializer(appointment)
            return Response({
                'message': 'Appointment cancelled',
                'appointment': serializer.data
            })
            
        except Appointment.DoesNotExist:
            return Response(
                {'error': 'Appointment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CreateAppointmentView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def post(self, request):
        try:
            serializer = AppointmentSerializer(data=request.data)
            if serializer.is_valid():
                appointment = serializer.save()
                return Response(
                    AppointmentSerializer(appointment).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SearchAppointmentsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        try:
            search_term = request.query_params.get('q', '')
            appointments = Appointment.objects.select_related(
                'patient__user', 'doctor__user'
            )
            
            if search_term:
                appointments = appointments.filter(
                    Q(patient__user__first_name__icontains=search_term) |
                    Q(patient__user__last_name__icontains=search_term) |
                    Q(doctor__user__first_name__icontains=search_term) |
                    Q(doctor__user__last_name__icontains=search_term) |
                    Q(reason__icontains=search_term) |
                    Q(notes__icontains=search_term)
                )
            
            serializer = AppointmentSerializer(appointments, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class HealthCheckView(APIView):
    def get(self, request):
        return Response({
            'status': 'ok',
            'service': 'Appointments API',
            'timestamp': timezone.now().isoformat()
        })

class AppointmentListCreateView(generics.ListCreateAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'appointment_type', 'priority', 'doctor']
    search_fields = ['patient__user__first_name', 'patient__user__last_name', 'reason']
    ordering_fields = ['appointment_date', 'created_at', 'priority']
    ordering = ['appointment_date']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AppointmentCreateSerializer
        return AppointmentSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Appointment.objects.select_related('patient', 'doctor', 'patient__user', 'doctor__user')
        
        if user.role == 'patient':
            return queryset.filter(patient__user=user)
        elif user.role == 'doctor':
            return queryset.filter(doctor__user=user)
        elif user.role in ['admin', 'staff']:
            return queryset
        else:
            return Appointment.objects.none()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class AppointmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AppointmentUpdateSerializer
        return AppointmentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return Appointment.objects.filter(patient__user=user)
        elif user.role == 'doctor':
            return Appointment.objects.filter(doctor__user=user)
        elif user.role in ['admin', 'staff']:
            return Appointment.objects.all()
        else:
            return Appointment.objects.none()

class PatientAppointmentsView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'appointment_type']
    ordering_fields = ['appointment_date']
    ordering = ['-appointment_date']

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        
        # Verify permission
        user = self.request.user
        if user.role == 'patient' and user.patient.id != patient_id:
            return Appointment.objects.none()
        
        return Appointment.objects.filter(patient_id=patient_id)

class DoctorAppointmentsView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'appointment_type', 'priority']
    ordering_fields = ['appointment_date']
    ordering = ['appointment_date']

    def get_queryset(self):
        doctor_id = self.kwargs['doctor_id']
        
        # Verify permission
        user = self.request.user
        if user.role == 'doctor' and user.doctor.id != doctor_id:
            return Appointment.objects.none()
        
        return Appointment.objects.filter(doctor_id=doctor_id)

class TodayAppointmentsView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        today = timezone.now().date()
        
        if user.role == 'doctor':
            return Appointment.objects.filter(
                doctor__user=user,
                appointment_date__date=today,
                status__in=['scheduled', 'confirmed', 'checked_in', 'in_progress']
            )
        elif user.role in ['admin', 'staff']:
            return Appointment.objects.filter(
                appointment_date__date=today,
                status__in=['scheduled', 'confirmed', 'checked_in', 'in_progress']
            )
        else:
            return Appointment.objects.none()

class UpcomingAppointmentsView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        now = timezone.now()
        
        if user.role == 'patient':
            return Appointment.objects.filter(
                patient__user=user,
                appointment_date__gte=now,
                status__in=['scheduled', 'confirmed']
            )
        elif user.role == 'doctor':
            return Appointment.objects.filter(
                doctor__user=user,
                appointment_date__gte=now,
                status__in=['scheduled', 'confirmed']
            )
        elif user.role in ['admin', 'staff']:
            return Appointment.objects.filter(
                appointment_date__gte=now,
                status__in=['scheduled', 'confirmed']
            )
        else:
            return Appointment.objects.none()

class AvailableSlotsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, doctor_id):
        date_str = request.GET.get('date')
        if not date_str:
            return Response(
                {'error': 'Date parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get available slots for the doctor on the given date
        slots = AppointmentSlot.objects.filter(
            doctor_id=doctor_id,
            slot_date=date,
            is_available=True
        ).exclude(current_bookings__gte=F('max_patients'))  
        
        serializer = AppointmentSlotSerializer(slots, many=True)
        return Response(serializer.data)

class UpdateAppointmentStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk)
            
            # Verify permission
            user = request.user
            if user.role == 'patient' and appointment.patient.user != user:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            elif user.role == 'doctor' and appointment.doctor.user != user:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = AppointmentUpdateSerializer(appointment, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(AppointmentSerializer(appointment).data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Appointment.DoesNotExist:
            return Response(
                {'error': 'Appointment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class AppointmentStatisticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['admin', 'staff', 'doctor']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Date range (default: current month)
        start_date = request.GET.get('start_date', timezone.now().replace(day=1).date())
        end_date = request.GET.get('end_date', timezone.now().date())
        
        # Filter by doctor if provided
        doctor_id = request.GET.get('doctor_id')
        appointments = Appointment.objects.filter(
            appointment_date__date__range=[start_date, end_date]
        )
        
        if doctor_id and request.user.role in ['admin', 'staff']:
            appointments = appointments.filter(doctor_id=doctor_id)
        elif request.user.role == 'doctor':
            appointments = appointments.filter(doctor__user=request.user)
        
        #Calculate average duration properly
        completed_appointments = appointments.filter(
            status='completed',
            actual_start_time__isnull=False,
            actual_end_time__isnull=False
        )
        
        total_duration = 0
        count = 0
        
        for appointment in completed_appointments:
            if appointment.actual_start_time and appointment.actual_end_time:
                duration = (appointment.actual_end_time - appointment.actual_start_time).total_seconds() / 60
                total_duration += duration
                count += 1
        
        average_duration = total_duration / count if count > 0 else 0
        
        stats = {
            'total_appointments': appointments.count(),
            'completed_appointments': appointments.filter(status='completed').count(),
            'cancelled_appointments': appointments.filter(status='cancelled').count(),
            'no_show_count': appointments.filter(status='no_show').count(),
            'average_duration': round(average_duration, 2)
        }
        
        serializer = AppointmentStatsSerializer(stats)
        return Response(serializer.data)

class CancelAppointmentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk)
            
            # Verify permission
            user = request.user
            if user.role == 'patient' and appointment.patient.user != user:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            elif user.role == 'doctor' and appointment.doctor.user != user:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            cancellation_reason = request.data.get('cancellation_reason', '')
            if not cancellation_reason:
                return Response(
                    {'error': 'Cancellation reason is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            appointment.status = 'cancelled'
            appointment.cancellation_reason = cancellation_reason
            appointment.save()
            
            return Response(AppointmentSerializer(appointment).data)
            
        except Appointment.DoesNotExist:
            return Response(
                {'error': 'Appointment not found'},
                status=status.HTTP_404_NOT_FOUND
            )