from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, F
from datetime import datetime, timedelta
from .models import Medication, MedicationDose, MedicationReminder, MedicationSchedule  
from .serializers import MedicationSerializer, MedicationDoseSerializer, MedicationReminderSerializer
from .tasks import schedule_medication_reminders

from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from django.core.paginator import Paginator
from django.http import JsonResponse

class MedicationViewSet(viewsets.ModelViewSet):
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]  
    def get_queryset(self):
        return Medication.objects.filter(patient=self.request.user)
    
    def perform_create(self, serializer):
        medication = serializer.save(patient=self.request.user)
        # Schedule reminders using the scheduler
        schedule_medication_reminders(medication.id)
    
    @action(detail=True, methods=['post'])
    def mark_taken(self, request, pk=None):
        medication = self.get_object()
        dose_time = timezone.now()
        
        #Find the correct scheduled time based on medication schedules
        scheduled_time = self._get_correct_scheduled_time(medication, dose_time)
        
        if not scheduled_time:
            return Response(
                {'error': 'No scheduled dose found for this time'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dose, created = MedicationDose.objects.get_or_create(
            medication=medication,
            scheduled_time=scheduled_time,
            defaults={
                'taken_time': dose_time,
                'is_taken': True,
                'is_skipped': False
            }
        )
        
        if not created:
            dose.taken_time = dose_time
            dose.is_taken = True
            dose.is_skipped = False
            dose.save()
        
        return Response({'status': 'Medication taken recorded'})
    
    @action(detail=True, methods=['post'])
    def skip_dose(self, request, pk=None):
        medication = self.get_object()
        dose_time = timezone.now()
        
        #  Find the correct scheduled time
        scheduled_time = self._get_correct_scheduled_time(medication, dose_time)
        
        if not scheduled_time:
            return Response(
                {'error': 'No scheduled dose found for this time'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dose, created = MedicationDose.objects.get_or_create(
            medication=medication,
            scheduled_time=scheduled_time,
            defaults={
                'is_taken': False,
                'is_skipped': True
            }
        )
        
        if not created:
            dose.is_skipped = True
            dose.is_taken = False
            dose.save()
        
        return Response({'status': 'Dose skipped'})
    
    def _get_correct_scheduled_time(self, medication, current_time):
        """
        Find the correct scheduled time based on medication schedules
        This is more accurate than just rounding to the hour
        """
        try:
            # Get today's day of week (0=Sunday, 6=Saturday)
            today_dow = str(current_time.weekday())
            
            # Find active schedules for today
            today_schedules = medication.schedules.filter(
                is_active=True,
                days_of_week__contains=today_dow
            )
            
            if today_schedules.exists():
                # Find the closest schedule time that hasn't passed yet
                for schedule in today_schedules:
                    # Combine today's date with schedule time
                    scheduled_datetime = datetime.combine(
                        current_time.date(), 
                        schedule.scheduled_time
                    ).replace(tzinfo=current_time.tzinfo)
                    
                    # Allow a 2-hour window for taking medication (before or after scheduled time)
                    time_diff = abs((current_time - scheduled_datetime).total_seconds())
                    if time_diff <= 7200:  # 2 hours in seconds
                        return scheduled_datetime
            
            # If no specific schedule found, use the simplified approach
            return current_time.replace(minute=0, second=0, microsecond=0)
            
        except Exception as e:
            # Fallback to simplified approach
            return current_time.replace(minute=0, second=0, microsecond=0)

class MedicationDoseViewSet(viewsets.ModelViewSet):
    serializer_class = MedicationDoseSerializer
    
    def get_queryset(self):
        return MedicationDose.objects.filter(medication__patient=self.request.user)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        today = timezone.now().date()
        doses = self.get_queryset().filter(
            scheduled_time__date=today
        ).order_by('scheduled_time')
        serializer = self.get_serializer(doses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming doses for today"""
        now = timezone.now()
        end_of_day = now.replace(hour=23, minute=59, second=59)
        
        doses = self.get_queryset().filter(
            scheduled_time__range=[now, end_of_day],
            is_taken=False,
            is_skipped=False
        ).order_by('scheduled_time')
        
        serializer = self.get_serializer(doses, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        """Add note to a dose"""
        dose = self.get_object()
        note = request.data.get('note', '')
        
        if note:
            dose.notes = note
            dose.save()
            return Response({'status': 'Note added'})
        else:
            return Response(
                {'error': 'Note content required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class MedicationReminderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MedicationReminderSerializer
    
    def get_queryset(self):
        return MedicationReminder.objects.filter(medication__patient=self.request.user)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending reminders"""
        pending_reminders = self.get_queryset().filter(
            reminder_time__gte=timezone.now(),
            is_sent=False
        ).order_by('reminder_time')
        
        serializer = self.get_serializer(pending_reminders, many=True)
        return Response(serializer.data)
    
    #ADMIN VIEWS
class AdminMedicationListView(generics.ListAPIView):
    """Admin view to list all medications"""
    permission_classes = [IsAdminUser]
    serializer_class = MedicationSerializer
    queryset = Medication.objects.all().order_by('-created_at')

class AdminCreateMedicationView(generics.CreateAPIView):
    """Admin view to create a new medication"""
    permission_classes = [IsAdminUser]
    serializer_class = MedicationSerializer

class AdminMedicationDetailView(generics.RetrieveAPIView):
    """Admin view to get medication details"""
    permission_classes = [IsAdminUser]
    serializer_class = MedicationSerializer
    queryset = Medication.objects.all()

class AdminUpdateMedicationView(generics.UpdateAPIView):
    """Admin view to update medication"""
    permission_classes = [IsAdminUser]
    serializer_class = MedicationSerializer
    queryset = Medication.objects.all()

class AdminDeleteMedicationView(generics.DestroyAPIView):
    """Admin view to delete medication"""
    permission_classes = [IsAdminUser]
    queryset = Medication.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'detail': 'Medication deleted successfully'}, status=status.HTTP_200_OK)

class AdminUpdateStockView(generics.UpdateAPIView):
    """Admin view to update medication stock"""
    permission_classes = [IsAdminUser]
    serializer_class = MedicationSerializer
    queryset = Medication.objects.all()

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        stock_quantity = request.data.get('stock_quantity')
        
        if stock_quantity is not None:
            try:
                instance.stock_quantity = int(stock_quantity)
                instance.save()
                serializer = self.get_serializer(instance)
                return Response(serializer.data)
            except ValueError:
                return Response(
                    {'error': 'Invalid stock quantity value'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            {'error': 'stock_quantity field is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

class AdminSearchMedicationsView(APIView):
    """Admin view to search medications"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        search_query = request.GET.get('q', '').strip()
        
        if not search_query:
            return Response(
                {'error': 'Search query is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        medications = Medication.objects.filter(
            Q(name__icontains=search_query) |
            Q(generic_name__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(manufacturer__icontains=search_query)
        ).order_by('-created_at')
        
        serializer = MedicationSerializer(medications, many=True)
        return Response(serializer.data)

class AdminMedicationStatisticsView(APIView):
    """Admin view to get medication statistics"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        total_medications = Medication.objects.count()
        
        low_stock = Medication.objects.filter(
            stock_quantity__lte=F('min_stock_level'),
            stock_quantity__gt=0
        ).count()
        
        out_of_stock = Medication.objects.filter(
            stock_quantity=0
        ).count()
        
        # Inventory value
        inventory_value = Medication.objects.aggregate(
            total_value=Sum(F('stock_quantity') * F('cost'))
        )['total_value'] or 0
        
        # Category distribution
        categories = Medication.objects.values('category').annotate(
            count=Count('id'),
            total_stock=Sum('stock_quantity')
        ).order_by('-count')
        
        # Recent additions (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_additions = Medication.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        # Expiring soon (within 90 days)
        ninety_days_later = timezone.now() + timedelta(days=90)
        expiring_soon = Medication.objects.filter(
            expiry_date__lte=ninety_days_later,
            expiry_date__gte=timezone.now()
        ).count()
        
        stats = {
            'total_medications': total_medications,
            'low_stock_count': low_stock,
            'out_of_stock_count': out_of_stock,
            'inventory_value': float(inventory_value),
            'recent_additions': recent_additions,
            'expiring_soon': expiring_soon,
            'categories': list(categories)
        }
        
        return Response(stats)

class AdminLowStockMedicationsView(APIView):
    """Admin view to get low stock medications"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        low_stock_medications = Medication.objects.filter(
            stock_quantity__lte=F('min_stock_level'),
            stock_quantity__gt=0
        ).order_by('stock_quantity')
        
        serializer = MedicationSerializer(low_stock_medications, many=True)
        return Response(serializer.data)

class AdminExpiringMedicationsView(APIView):
    """Admin view to get expiring soon medications"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        ninety_days_later = timezone.now() + timedelta(days=90)
        
        expiring_medications = Medication.objects.filter(
            expiry_date__lte=ninety_days_later,
            expiry_date__gte=timezone.now()
        ).order_by('expiry_date')
        
        serializer = MedicationSerializer(expiring_medications, many=True)
        return Response(serializer.data)   