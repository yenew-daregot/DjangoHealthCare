import logging
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.db.models import Q
from rest_framework import generics, permissions, status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound

from .models import Doctor, DoctorSchedule, ScheduleException, DoctorAvailability
from .schedule_serializers import (
    DoctorScheduleSerializer, ScheduleExceptionSerializer,
    DoctorAvailabilitySerializer, WeeklyScheduleSerializer,
    ScheduleCreateSerializer, AvailableSlotsSerializer
)

logger = logging.getLogger(__name__)


class DoctorScheduleListCreateView(generics.ListCreateAPIView):
    """List and create doctor schedules"""
    serializer_class = DoctorScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        try:
            doctor = Doctor.objects.get(user=self.request.user)
            return DoctorSchedule.objects.filter(doctor=doctor)
        except Doctor.DoesNotExist:
            return DoctorSchedule.objects.none()
    
    def perform_create(self, serializer):
        try:
            doctor = Doctor.objects.get(user=self.request.user)
            serializer.save(doctor=doctor)
        except Doctor.DoesNotExist:
            raise serializers.ValidationError("Doctor profile not found")


class DoctorScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete specific schedule"""
    serializer_class = DoctorScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        try:
            doctor = Doctor.objects.get(user=self.request.user)
            return DoctorSchedule.objects.filter(doctor=doctor)
        except Doctor.DoesNotExist:
            return DoctorSchedule.objects.none()


class WeeklyScheduleView(APIView):
    """Get doctor's complete weekly schedule"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            return Response(
                {'error': 'Doctor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all schedules grouped by day
        schedules = DoctorSchedule.objects.filter(doctor=doctor, is_active=True)
        
        weekly_data = {
            'monday': [],
            'tuesday': [],
            'wednesday': [],
            'thursday': [],
            'friday': [],
            'saturday': [],
            'sunday': []
        }
        
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for schedule in schedules:
            day_name = day_names[schedule.day_of_week]
            serializer = DoctorScheduleSerializer(schedule, context={'request': request})
            weekly_data[day_name].append(serializer.data)
        
        # Get recent exceptions (next 30 days)
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=30)
        exceptions = ScheduleException.objects.filter(
            doctor=doctor,
            date__range=[start_date, end_date]
        )
        
        # Get availability status
        availability, created = DoctorAvailability.objects.get_or_create(
            doctor=doctor,
            defaults={'is_online': False}
        )
        
        weekly_data['exceptions'] = ScheduleExceptionSerializer(exceptions, many=True).data
        weekly_data['availability'] = DoctorAvailabilitySerializer(availability).data
        weekly_data['doctor_info'] = {
            'id': doctor.id,
            'name': doctor.full_name,
            'specialization': doctor.specialization.name if doctor.specialization else 'General'
        }
        
        return Response(weekly_data)


class BulkScheduleCreateView(APIView):
    """Create multiple schedule entries at once"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            return Response(
                {'error': 'Doctor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ScheduleCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            schedules = serializer.save()
            response_data = DoctorScheduleSerializer(schedules, many=True).data
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScheduleExceptionListCreateView(generics.ListCreateAPIView):
    """List and create schedule exceptions"""
    serializer_class = ScheduleExceptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        try:
            doctor = Doctor.objects.get(user=self.request.user)
            # Get exceptions for next 90 days by default
            start_date = timezone.now().date()
            end_date = start_date + timedelta(days=90)
            
            queryset = ScheduleException.objects.filter(doctor=doctor)
            
            # Filter by date range if provided
            date_from = self.request.query_params.get('date_from')
            date_to = self.request.query_params.get('date_to')
            
            if date_from:
                queryset = queryset.filter(date__gte=date_from)
            else:
                queryset = queryset.filter(date__gte=start_date)
            
            if date_to:
                queryset = queryset.filter(date__lte=date_to)
            else:
                queryset = queryset.filter(date__lte=end_date)
            
            return queryset.order_by('date', 'start_time')
            
        except Doctor.DoesNotExist:
            return ScheduleException.objects.none()
    
    def perform_create(self, serializer):
        try:
            doctor = Doctor.objects.get(user=self.request.user)
            serializer.save(doctor=doctor)
        except Doctor.DoesNotExist:
            raise serializers.ValidationError("Doctor profile not found")


class ScheduleExceptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete specific schedule exception"""
    serializer_class = ScheduleExceptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        try:
            doctor = Doctor.objects.get(user=self.request.user)
            return ScheduleException.objects.filter(doctor=doctor)
        except Doctor.DoesNotExist:
            return ScheduleException.objects.none()


class DoctorAvailabilityView(generics.RetrieveUpdateAPIView):
    """Get and update doctor availability status"""
    serializer_class = DoctorAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        try:
            doctor = Doctor.objects.get(user=self.request.user)
            availability, created = DoctorAvailability.objects.get_or_create(
                doctor=doctor,
                defaults={'is_online': False}
            )
            return availability
        except Doctor.DoesNotExist:
            raise NotFound("Doctor profile not found")


class AvailableSlotsView(APIView):
    """Get available time slots for a specific date"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            return Response(
                {'error': 'Doctor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get date parameter (default to today)
        date_str = request.query_params.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            target_date = timezone.now().date()
        
        # Get day of week (0=Monday, 6=Sunday)
        day_of_week = target_date.weekday()
        
        # Get schedule for this day
        schedules = DoctorSchedule.objects.filter(
            doctor=doctor,
            day_of_week=day_of_week,
            is_active=True
        )
        
        if not schedules.exists():
            return Response({
                'date': target_date,
                'slots': [],
                'message': 'No schedule found for this day'
            })
        
        # Check for exceptions on this date
        exceptions = ScheduleException.objects.filter(
            doctor=doctor,
            date=target_date
        )
        
        all_slots = []
        
        for schedule in schedules:
            # Check if this schedule is blocked by an exception
            is_blocked = False
            for exception in exceptions:
                if exception.exception_type in ['holiday', 'blocked'] and not exception.is_available:
                    if not exception.start_time or not exception.end_time:
                        # Full day exception
                        is_blocked = True
                        break
                    # Check if schedule overlaps with exception
                    if not (schedule.end_time <= exception.start_time or schedule.start_time >= exception.end_time):
                        is_blocked = True
                        break
            
            if not is_blocked:
                slots = schedule.get_available_slots(target_date)
                all_slots.extend(slots)
        
        # Sort slots by time
        all_slots.sort(key=lambda x: x['start_time'])
        
        return Response({
            'date': target_date,
            'slots': all_slots,
            'total_slots': len(all_slots)
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_availability(request):
    """Toggle doctor's online/offline status"""
    try:
        doctor = Doctor.objects.get(user=request.user)
        availability, created = DoctorAvailability.objects.get_or_create(
            doctor=doctor,
            defaults={'is_online': False}
        )
        
        # Toggle status
        availability.is_online = not availability.is_online
        availability.save()
        
        return Response({
            'is_online': availability.is_online,
            'message': f"Status changed to {'Online' if availability.is_online else 'Offline'}"
        })
        
    except Doctor.DoesNotExist:
        return Response(
            {'error': 'Doctor profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def schedule_summary(request):
    """Get schedule summary for dashboard"""
    try:
        doctor = Doctor.objects.get(user=request.user)
        
        # Get total scheduled hours this week
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        
        schedules = DoctorSchedule.objects.filter(doctor=doctor, is_active=True)
        
        total_hours = 0
        active_days = 0
        
        for schedule in schedules:
            # Calculate hours for this schedule
            start_datetime = datetime.combine(today, schedule.start_time)
            end_datetime = datetime.combine(today, schedule.end_time)
            duration = end_datetime - start_datetime
            
            # Subtract break time if exists
            if schedule.break_start and schedule.break_end:
                break_start_datetime = datetime.combine(today, schedule.break_start)
                break_end_datetime = datetime.combine(today, schedule.break_end)
                break_duration = break_end_datetime - break_start_datetime
                duration -= break_duration
            
            total_hours += duration.total_seconds() / 3600
            active_days += 1
        
        # Get upcoming exceptions
        upcoming_exceptions = ScheduleException.objects.filter(
            doctor=doctor,
            date__gte=today,
            date__lte=today + timedelta(days=7)
        ).count()
        
        # Get availability status
        availability = DoctorAvailability.objects.filter(doctor=doctor).first()
        
        return Response({
            'total_weekly_hours': round(total_hours, 1),
            'active_days': active_days,
            'upcoming_exceptions': upcoming_exceptions,
            'is_online': availability.is_online if availability else False,
            'last_updated': availability.updated_at if availability else None
        })
        
    except Doctor.DoesNotExist:
        return Response(
            {'error': 'Doctor profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )