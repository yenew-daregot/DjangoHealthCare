import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Q, Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

# Import from other apps - handle missing imports gracefully
try:
    from appointments.models import Appointment
    HAS_APPOINTMENTS = True
except ImportError:
    Appointment = None
    HAS_APPOINTMENTS = False

try:
    from patients.models import Patient
    HAS_PATIENTS = True
except ImportError:
    Patient = None
    HAS_PATIENTS = False

try:
    from prescriptions.models import Prescription
    HAS_PRESCRIPTIONS = True
except ImportError:
    Prescription = None
    HAS_PRESCRIPTIONS = False

from .models import Doctor, Specialization
from .serializers import DoctorSerializer, SpecializationSerializer, DoctorCreateSerializer, UserSerializer

# Initialize logger (ONLY ONCE)
logger = logging.getLogger(__name__)


class DoctorListView(generics.ListAPIView):
    serializer_class = DoctorSerializer
    permission_classes = [permissions.AllowAny] 
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['specialization', 'is_available', 'is_verified']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'qualification']
    ordering_fields = ['consultation_fee', 'years_of_experience', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        # For debugging, return all available and verified doctors
        return Doctor.objects.filter(is_available=True, is_verified=True)
        

class DoctorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a doctor instance.
    """
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # Admin/staff can see all doctors
        if user.role in ['ADMIN', 'STAFF']:
            return Doctor.objects.all().select_related('user', 'specialization')
        # Doctors can see themselves + available doctors
        elif user.role == 'DOCTOR':
            return Doctor.objects.filter(
                Q(user=user) | Q(is_available=True, is_verified=True)
            ).select_related('user', 'specialization')
        # Allow viewing any doctor profile for booking appointments
        elif user.role == 'PATIENT':
            return Doctor.objects.all().select_related('user', 'specialization')
        
        return Doctor.objects.none()
    
    def perform_update(self, serializer):
        user = self.request.user
        doctor = self.get_object()
        
        # Only admins and the doctor themselves can update
        if user.role == 'ADMIN' or (user.role == 'DOCTOR' and doctor.user == user):
            serializer.save()
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to update this doctor profile.")
    
    def perform_destroy(self, instance):
        user = self.request.user
        
        # Only admins can delete doctor profiles
        if user.role != 'ADMIN':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only administrators can delete doctor profiles.")
        
        # Also delete the associated user
        instance.user.delete()


class SpecializationListView(generics.ListAPIView):
    queryset = Specialization.objects.filter(is_active=True)
    serializer_class = SpecializationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class DoctorProfileView(generics.RetrieveUpdateAPIView):
    """View for doctors to retrieve and update their own profile."""
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'put', 'patch', 'options', 'head'] 

    def get_object(self):
        """Get the doctor profile for the currently authenticated user."""
        try:
            return Doctor.objects.select_related('user', 'specialization').get(user=self.request.user)
        except Doctor.DoesNotExist:
            raise NotFound({
                'error': 'Doctor profile not found',
                'message': 'Please complete your doctor profile setup.'
            })
    
    def perform_update(self, serializer):
        """Ensure users can only update their own profile."""
        if serializer.instance.user != self.request.user:
            raise PermissionDenied({
                'error': 'Permission denied',
                'message': 'You can only update your own profile.'
            })
        
        logger.info(
            f"Doctor profile updated: {self.request.user.username}",
            extra={'doctor_id': serializer.instance.doctor_id}
        )       
        serializer.save()


class DoctorCreateView(generics.CreateAPIView):
    serializer_class = DoctorCreateSerializer  
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Only allow users with doctor role to create doctor profiles
        if self.request.user.role != 'DOCTOR':
            raise PermissionDenied(
                "Only users with doctor role can create doctor profiles."
            )
        # Check if user already has a doctor profile
        if Doctor.objects.filter(user=self.request.user).exists():
            raise ValidationError("Doctor profile already exists for this user.")
        # Pass request context for auto user assignment
        serializer.save()


class AvailableDoctorsView(generics.ListAPIView):
    """View specifically for available and verified doctors"""
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Doctor.objects.filter(is_available=True, is_verified=True)


class DoctorsBySpecializationView(generics.ListAPIView):
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        specialization_id = self.kwargs['specialization_id']
        return Doctor.objects.filter(
            specialization_id=specialization_id,
            is_available=True,
            is_verified=True
        )


class DoctorDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Simple dashboard view - to be implemented"""
        try:
            doctor = Doctor.objects.get(user=request.user)
            return Response({
                'message': 'Doctor dashboard is working!',
                'doctor': {
                    'id': doctor.id,
                    'name': doctor.full_name,
                    'specialization': doctor.specialization.name if doctor.specialization else 'General'
                }
            })
        except Doctor.DoesNotExist:
            return Response(
                {'error': 'Doctor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class DoctorAppointmentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get appointments for the current doctor"""
        logger.info(
            f"DoctorAppointmentsView accessed by user: {request.user.username}",
            extra={
                'user_id': request.user.id,
                'user_role': request.user.role,
                'method': request.method,
                'query_params': dict(request.GET)
            }
        )
        
        try:
            if not self.is_doctor(request.user):
                logger.warning(
                    f"Non-doctor user attempted to access appointments: {request.user.username}",
                    extra={'user_role': request.user.role}
                )
                return Response(
                    {'error': 'Access denied. Doctor role required.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Exception as e:
            logger.error(f"Error in role check: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Internal server error in role validation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            doctor = Doctor.objects.get(user=request.user)
            logger.debug(f"Doctor found: {doctor.id}")
        except Doctor.DoesNotExist:
            logger.warning(
                f"Doctor profile not found for user: {request.user.username}"
            )
            return Response(
                {'error': 'Doctor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if appointments app is installed and has data
        if not HAS_APPOINTMENTS:
            logger.info(" no appointments found")
            return Response({
                'count': 0,
                'next': None,
                'previous': None,
                'results': [],
                'doctor_info': {
                    'id': doctor.id,
                    'name': doctor.full_name,
                    'specialization': doctor.specialization.name if doctor.specialization else 'General'
                }
            })
        
        try:
            # Get pagination parameters
            try:
                page = int(request.GET.get('page', 1))
                page_size = int(request.GET.get('page_size', 10))
            except ValueError as e:
                logger.warning(f"Invalid pagination parameters: {str(e)}")
                page = 1
                page_size = 10
            
            status_filter = request.GET.get('status', 'all')
            search = request.GET.get('search', '').strip()
            
            logger.debug(
                f"Pagination params: page={page}, page_size={page_size}, "
                f"status={status_filter}, search='{search}'"
            )
            
            # Build base queryset 
            queryset = Appointment.objects.all()
            
            # Try to find appointments related to this doctor
            # Check different possible field names
            doctor_appointments = None
            
            # Direct doctor field
            if hasattr(Appointment, 'doctor') and Appointment.doctor.field.related_model == Doctor:
                doctor_appointments = queryset.filter(doctor=doctor)
                logger.debug("Found appointments via 'doctor' field")
            
            # doctor_user field
            elif hasattr(Appointment, 'doctor_user'):
                doctor_appointments = queryset.filter(doctor_user=doctor.user)
                logger.debug("Found appointments via 'doctor_user' field")
            
            # treating_doctor field
            elif hasattr(Appointment, 'treating_doctor'):
                doctor_appointments = queryset.filter(treating_doctor=doctor)
                logger.debug("Found appointments via 'treating_doctor' field")
            
            # assigned_doctor field
            elif hasattr(Appointment, 'assigned_doctor'):
                doctor_appointments = queryset.filter(assigned_doctor=doctor)
                logger.debug("Found appointments via 'assigned_doctor' field")
            
            # Scan all foreign keys to Doctor
            else:
                for field in Appointment._meta.get_fields():
                    if (hasattr(field, 'related_model') and 
                        field.related_model == Doctor):
                        doctor_appointments = queryset.filter(**{field.name: doctor})
                        logger.debug(f"Found appointments via '{field.name}' field")
                        break
            
            if doctor_appointments is None:
                logger.warning(f"No appointment relationship found for doctor {doctor.id}")
                # Return empty results instead of error
                return Response({
                    'count': 0,
                    'next': None,
                    'previous': None,
                    'results': [],
                    'doctor_info': {
                        'id': doctor.id,
                        'name': doctor.full_name,
                        'specialization': doctor.specialization.name if doctor.specialization else 'General'
                    },
                    'message': 'No appointments found for this doctor'
                })
            
            # Apply status filter
            if status_filter != 'all' and status_filter:
                # Handle comma-separated statuses
                if ',' in status_filter:
                    statuses = [s.strip() for s in status_filter.split(',')]
                    doctor_appointments = doctor_appointments.filter(status__in=statuses)
                else:
                    doctor_appointments = doctor_appointments.filter(status=status_filter)
            
            # Apply search filter
            if search:
                search_query = Q()
                # Try patient name fields
                if hasattr(Appointment, 'patient'):
                    patient_model = Appointment.patient.field.related_model
                    if hasattr(patient_model, 'user'):
                        search_query |= Q(patient__user__first_name__icontains=search)
                        search_query |= Q(patient__user__last_name__icontains=search)
                    else:
                        # Try direct patient name fields
                        for field in ['name', 'full_name', 'first_name', 'last_name']:
                            if hasattr(patient_model, field):
                                search_query |= Q(**{f'patient__{field}__icontains': search})
                
                # Search in appointment fields
                for field in ['reason', 'notes', 'appointment_type']:
                    if hasattr(Appointment, field):
                        search_query |= Q(**{f'{field}__icontains': search})
                
                doctor_appointments = doctor_appointments.filter(search_query)
            
            # Order by date (most recent first)
            order_by_fields = []
            if hasattr(Appointment, 'appointment_date'):
                order_by_fields.append('-appointment_date')
            if hasattr(Appointment, 'appointment_time'):
                order_by_fields.append('-appointment_time')
            if hasattr(Appointment, 'created_at'):
                order_by_fields.append('-created_at')
            
            if order_by_fields:
                doctor_appointments = doctor_appointments.order_by(*order_by_fields)
            
            # Get total count
            total_count = doctor_appointments.count()
            logger.debug(f"Total appointments found: {total_count}")
            
            # Apply pagination
            start = (page - 1) * page_size
            end = start + page_size
            appointments = doctor_appointments[start:end]
            
            # Serialize appointments
            appointments_data = []
            for apt in appointments:
                try:
                    appointment_data = {
                        'id': apt.id,
                        'status': apt.status or 'pending',
                        'appointment_type': apt.appointment_type or 'Consultation',
                        'reason': apt.reason or '',
                        'notes': apt.notes or '',
                        'priority': getattr(apt, 'priority', 'normal'),
                        'created_at': apt.created_at.isoformat() if hasattr(apt, 'created_at') and apt.created_at else None,
                        'cancellation_reason': getattr(apt, 'cancellation_reason', None),
                        'duration': getattr(apt, 'duration', 30)
                    }
                    
                    # Add date/time fields
                    if hasattr(apt, 'appointment_date') and apt.appointment_date:
                        appointment_data['appointment_date'] = apt.appointment_date.isoformat()
                    if hasattr(apt, 'appointment_time') and apt.appointment_time:
                        appointment_data['appointment_time'] = str(apt.appointment_time)
                    
                    # Add patient info
                    if hasattr(apt, 'patient') and apt.patient:
                        appointment_data['patient'] = self.serialize_patient(apt)
                    else:
                        appointment_data['patient'] = {
                            'id': None,
                            'name': 'Unknown Patient',
                            'email': 'N/A'
                        }
                    
                    appointments_data.append(appointment_data)
                    
                except Exception as e:
                    logger.warning(
                        f"Error serializing appointment {apt.id}: {str(e)}",
                        extra={'appointment_id': apt.id}
                    )
                    # Add minimal data
                    appointments_data.append({
                        'id': apt.id,
                        'status': 'error',
                        'patient': {'name': 'Error loading patient', 'email': 'N/A'}
                    })
            
            # Build response URLs
            base_url = request.build_absolute_uri('/api/doctors/appointments/')
            next_url = None
            previous_url = None
            
            if end < total_count:
                next_url = f"{base_url}?page={page + 1}&page_size={page_size}"
                if status_filter != 'all':
                    next_url += f"&status={status_filter}"
                if search:
                    next_url += f"&search={search}"
            
            if page > 1:
                previous_url = f"{base_url}?page={page - 1}&page_size={page_size}"
                if status_filter != 'all':
                    previous_url += f"&status={status_filter}"
                if search:
                    previous_url += f"&search={search}"
            
            response_data = {
                'count': total_count,
                'next': next_url,
                'previous': previous_url,
                'results': appointments_data,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size if page_size > 0 else 0,
                'doctor_info': {
                    'id': doctor.id,
                    'name': doctor.full_name,
                    'specialization': doctor.specialization.name if doctor.specialization else 'General'
                }
            }
            
            logger.info(
                f"Successfully returned {len(appointments_data)} appointments for doctor {doctor.id}"
            )
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(
                f"Error in DoctorAppointmentsView: {str(e)}",
                exc_info=True,
                extra={
                    'doctor_id': doctor.id,
                    'user_id': request.user.id
                }
            )
            return Response(
                {
                    'error': 'Failed to load appointments',
                    'detail': str(e) if settings.DEBUG else 'Internal server error',
                    'doctor_info': {
                        'id': doctor.id,
                        'name': doctor.full_name,
                        'specialization': doctor.specialization.name if doctor.specialization else 'General'
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def is_doctor(self, user):
        """Check if user is a doctor"""
        if hasattr(user, 'role'):
            role = user.role
            if isinstance(role, str):
                return role.upper() == 'DOCTOR'
            return role == 'DOCTOR' or str(role).upper() == 'DOCTOR'
        return False
    
    def serialize_patient(self, appointment):
        """Serialize patient info with error handling"""
        try:
            patient = appointment.patient
            if not patient:
                return {
                    'id': None,
                    'name': 'Unknown Patient',
                    'email': 'N/A',
                    'phone': 'N/A',
                    'user': None
                }
            
            patient_data = {
                'id': patient.id,
                'name': 'Unknown Patient',
                'email': 'N/A',
                'phone': 'N/A',
                'user': None
            }
            
            # Try to get user info
            if hasattr(patient, 'user') and patient.user:
                user = patient.user
                patient_data.update({
                    'user': {
                        'id': user.id,
                        'first_name': user.first_name or '',
                        'last_name': user.last_name or '',
                        'email': user.email or 'N/A',
                        'phone_number': getattr(user, 'phone_number', 'N/A')
                    },
                    'name': f"{user.first_name or ''} {user.last_name or ''}".strip() or 'Patient',
                    'email': user.email or 'N/A',
                    'phone': getattr(user, 'phone_number', 'N/A')
                })
            else:
                # Try direct fields on patient
                for field in ['full_name', 'name', 'email', 'phone_number', 'phone']:
                    if hasattr(patient, field):
                        value = getattr(patient, field)
                        if value:
                            if field in ['full_name', 'name']:
                                patient_data['name'] = value
                            elif field == 'email':
                                patient_data['email'] = value
                            elif field in ['phone_number', 'phone']:
                                patient_data['phone'] = value
            
            return patient_data
            
        except Exception as e:
            logger.warning(f"Error serializing patient: {str(e)}")
            return {
                'id': None,
                'name': 'Error loading patient',
                'email': 'N/A',
                'phone': 'N/A',
                'user': None
            }


class DoctorDashboardDataView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get comprehensive dashboard data for doctor"""
        try:
            # Get doctor profile
            doctor = Doctor.objects.get(user=request.user)
            
            # Get basic stats
            today = timezone.now().date()
            
            # Initialize stats
            stats = {
                'today_patients': 0,
                'completed_appointments': 0,
                'pending_appointments': 0,
                'total_patients': 0,
                'monthly_revenue': doctor.consultation_fee * 20  # Estimate
            }
            
            # Get appointments if available
            if HAS_APPOINTMENTS:
                try:
                    # We need to find the correct field name that links Appointment to Doctor
                    # Try different field names
                    doctor_filter_kwargs = {}
                    
                    # Try to find the correct field name
                    if hasattr(Appointment, 'doctor'):
                        doctor_filter_kwargs = {'doctor': doctor}
                    elif hasattr(Appointment, 'doctor_user'):
                        doctor_filter_kwargs = {'doctor_user': doctor.user}
                    elif hasattr(Appointment, 'treating_doctor'):
                        doctor_filter_kwargs = {'treating_doctor': doctor}
                    elif hasattr(Appointment, 'assigned_doctor'):
                        doctor_filter_kwargs = {'assigned_doctor': doctor}
                    else:
                        # Scan for any Doctor foreign key
                        for field in Appointment._meta.get_fields():
                            if (hasattr(field, 'related_model') and 
                                field.related_model == Doctor):
                                doctor_filter_kwargs = {field.name: doctor}
                                break
                    
                    # Only proceed if we found a valid field
                    if doctor_filter_kwargs:
                        # Get today's appointments
                        today_appointments = Appointment.objects.filter(
                            **doctor_filter_kwargs,
                            appointment_date=today
                        ).count()
                        stats['today_patients'] = today_appointments
                        
                        # Get completed appointments (this month)
                        month_start = today.replace(day=1)
                        completed = Appointment.objects.filter(
                            **doctor_filter_kwargs,
                            status='completed',
                            appointment_date__gte=month_start
                        ).count()
                        stats['completed_appointments'] = completed
                        
                        # Get pending appointments
                        pending = Appointment.objects.filter(
                            **doctor_filter_kwargs,
                            status='pending'
                        ).count()
                        stats['pending_appointments'] = pending
                        
                        # Get total patients (estimate from appointments)
                        unique_patients = Appointment.objects.filter(
                            **doctor_filter_kwargs
                        ).values('patient').distinct().count()
                        stats['total_patients'] = unique_patients
                    else:
                        logger.warning("No appointment relationship found for dashboard stats")
                        
                except Exception as e:
                    logger.warning(f"Could not fetch appointment stats: {str(e)}")
            
            # Prepare response data
            dashboard_data = {
                'doctor_info': {
                    'id': doctor.id,
                    'full_name': doctor.full_name,
                    'specialization': doctor.specialization.name if doctor.specialization else 'General Medicine',
                    'consultation_fee': doctor.consultation_fee,
                    'years_of_experience': doctor.years_of_experience,
                    'rating': 4.5,  # Default
                    'reviews_count': 0,
                    'is_available': doctor.is_available
                },
                'quick_stats': stats,
                'doctor_id': doctor.id
            }
            
            return Response(dashboard_data)
            
        except Doctor.DoesNotExist:
            return Response(
                {'error': 'Doctor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error in dashboard data: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to load dashboard data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DoctorRegistrationView(APIView):
    """
    Combined endpoint for registering a doctor (user + doctor profile)
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        logger.info(f"Doctor registration attempt: {request.data.get('username')}")
        
        try:
            # Import here to avoid circular imports
            from users.serializers import RegisterSerializer
            from .serializers import DoctorCreateSerializer, DoctorSerializer
            
            # Validate and create user
            user_serializer = RegisterSerializer(data=request.data)
            user_serializer.is_valid(raise_exception=True)
            
            # Ensure role is set to doctor
            user_data = user_serializer.validated_data.copy()
            user_data['role'] = 'DOCTOR'
            
            # Create user
            user = user_serializer.create(user_data)
            logger.info(f"User created: {user.username} (ID: {user.id})")
            
            # Create doctor profile
            doctor_data = {
                'specialization_id': request.data.get('specialization_id'),
                'license_number': request.data.get('license_number'),
                'qualification': request.data.get('qualification'),
                'years_of_experience': request.data.get('years_of_experience', 0),
                'consultation_fee': request.data.get('consultation_fee', 0),
                'bio': request.data.get('bio', ''),
                'address': request.data.get('address', ''),
                'consultation_hours': request.data.get('consultation_hours', {}),
                'user': user.id  # Pass user ID instead of full object
            }
            
            # Remove None values
            doctor_data = {k: v for k, v in doctor_data.items() if v is not None}
            
            doctor_serializer = DoctorCreateSerializer(
                data=doctor_data,
                context={'request': request}  # Pass context for auto-assigning user
            )
            doctor_serializer.is_valid(raise_exception=True)
            doctor = doctor_serializer.save()
            logger.info(f"Doctor profile created: Dr. {user.get_full_name()}")
            
            # Return combined response
            response_data = {
                'message': 'Doctor registration successful',
                'user': UserSerializer(user, context={'request': request}).data,
                'doctor': DoctorSerializer(doctor, context={'request': request}).data,
                'tokens': self.get_auth_tokens(user)  
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            logger.error(f"Validation error in doctor registration: {str(e)}")
            return Response(
                {'error': 'Validation failed', 'details': e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error in doctor registration: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Registration failed', 'detail': str(e) if settings.DEBUG else 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_auth_tokens(self, user):
        """Get authentication tokens if using token auth"""
        try:
            # If using Simple JWT
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        except:
            return None


class UserInfoDebugView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            doctor_exists = hasattr(request.user, 'doctor')
            doctor_id = request.user.doctor.id if doctor_exists else None
            
            # Debug appointment model structure
            appointment_debug = {}
            if HAS_APPOINTMENTS:
                appointment_fields = [f.name for f in Appointment._meta.get_fields()]
                appointment_debug = {
                    'model_exists': True,
                    'fields': appointment_fields,
                    'sample_data_count': Appointment.objects.count()
                }
            else:
                appointment_debug = {'model_exists': False}
            
            return Response({
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'role': request.user.role,
                'is_authenticated': request.user.is_authenticated,
                'has_doctor_profile': doctor_exists,
                'doctor_profile_id': doctor_id,
                'appointment_model': appointment_debug,
                'timestamp': timezone.now().isoformat()
            })
        except Exception as e:
            return Response({
                'error': str(e),
                'username': request.user.username if request.user else 'Unknown'
            })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def doctor_stats(request):
    """Get statistics about doctors"""
    if request.user.role not in ['ADMIN', 'STAFF']:
        return Response(
            {'error': 'Permission denied'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    stats = {
        'total_doctors': Doctor.objects.count(),
        'available_doctors': Doctor.objects.filter(is_available=True).count(),
        'verified_doctors': Doctor.objects.filter(is_verified=True).count(),
        'specializations_count': Specialization.objects.filter(is_active=True).count(),
    }
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # Allow public access for patient dashboard
def public_doctor_stats(request):
    """Get public statistics about doctors for patient dashboard"""
    try:
        # Get basic doctor statistics that are safe to show publicly
        total_doctors = Doctor.objects.filter(is_verified=True).count()
        available_doctors = Doctor.objects.filter(is_available=True, is_verified=True).count()
        verified_doctors = Doctor.objects.filter(is_verified=True).count()
        
        stats = {
            'total_doctors': total_doctors,
            'available_doctors': available_doctors,
            'verified_doctors': verified_doctors,
        }
        
        logger.info(f"Public doctor stats requested: {stats}")
        return Response(stats)
        
    except Exception as e:
        logger.error(f"Error fetching public doctor stats: {str(e)}")
        # Return fallback stats if there's an error
        return Response({
            'total_doctors': 0,
            'available_doctors': 0,
            'verified_doctors': 0,
        })


# Add public test endpoints
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def public_test(request):
    """Public endpoint to test if Django is reachable"""
    # Also test doctors data
    doctors_count = Doctor.objects.count()
    available_doctors = Doctor.objects.filter(is_available=True, is_verified=True).count()
    
    return Response({
        'status': 'success',
        'message': 'Django API is working!',
        'timestamp': timezone.now().isoformat(),
        'doctors_info': {
            'total_doctors': doctors_count,
            'available_verified_doctors': available_doctors
        },
        'endpoints': {
            'doctor_appointments': '/api/doctors/appointments/',
            'doctor_dashboard': '/api/doctors/dashboard/',
            'doctors_list': '/api/doctors/',
        }
    })


@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'user': request.user.username if request.user.is_authenticated else 'anonymous'
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def debug_appointments(request):
    """Debug appointments endpoint"""
    return Response({
        'doctor_exists': hasattr(request.user, 'doctor'),
        'user': request.user.username,
        'role': request.user.role
    })
# Helper function (if needed, but currently not used by any class)
def get_appointment_filter(doctor):
    """Determine how to filter appointments for this doctor"""
    if not HAS_APPOINTMENTS:
        return None
    return {'doctor': doctor}

class DoctorPatientsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get patients for the current doctor based on appointments"""
        logger.info(
            f"DoctorPatientsView accessed by user: {request.user.username}",
            extra={
                'user_id': request.user.id,
                'user_role': request.user.role,
                'method': request.method,
                'query_params': dict(request.GET)
            }
        )
        
        try:
            if not self.is_doctor(request.user):
                logger.warning(
                    f"Non-doctor user attempted to access patients: {request.user.username}",
                    extra={'user_role': request.user.role}
                )
                return Response(
                    {'error': 'Access denied. Doctor role required.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Exception as e:
            logger.error(f"Error in role check: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Internal server error in role validation'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            doctor = Doctor.objects.get(user=request.user)
            logger.debug(f"Doctor found: {doctor.id}")
        except Doctor.DoesNotExist:
            logger.warning(
                f"Doctor profile not found for user: {request.user.username}"
            )
            return Response(
                {'error': 'Doctor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if appointments app is installed
        if not HAS_APPOINTMENTS:
            logger.info("Appointments app not available")
            return Response({
                'count': 0,
                'results': [],
                'doctor_info': {
                    'id': doctor.id,
                    'name': doctor.full_name,
                    'specialization': doctor.specialization.name if doctor.specialization else 'General'
                }
            })
        
        try:
            # Get search parameter
            search = request.GET.get('search', '').strip()
            
            # Build base queryset for appointments
            queryset = Appointment.objects.all()
            
            # Find appointments related to this doctor
            doctor_appointments = None
            
            # Try different field names to find doctor appointments
            if hasattr(Appointment, 'doctor') and Appointment.doctor.field.related_model == Doctor:
                doctor_appointments = queryset.filter(doctor=doctor)
                logger.debug("Found appointments via 'doctor' field")
            elif hasattr(Appointment, 'doctor_user'):
                doctor_appointments = queryset.filter(doctor_user=doctor.user)
                logger.debug("Found appointments via 'doctor_user' field")
            elif hasattr(Appointment, 'treating_doctor'):
                doctor_appointments = queryset.filter(treating_doctor=doctor)
                logger.debug("Found appointments via 'treating_doctor' field")
            elif hasattr(Appointment, 'assigned_doctor'):
                doctor_appointments = queryset.filter(assigned_doctor=doctor)
                logger.debug("Found appointments via 'assigned_doctor' field")
            else:
                # Scan all foreign keys to Doctor
                for field in Appointment._meta.get_fields():
                    if (hasattr(field, 'related_model') and 
                        field.related_model == Doctor):
                        doctor_appointments = queryset.filter(**{field.name: doctor})
                        logger.debug(f"Found appointments via '{field.name}' field")
                        break
            
            if doctor_appointments is None:
                logger.warning(f"No appointment relationship found for doctor {doctor.id}")
                return Response({
                    'count': 0,
                    'results': [],
                    'doctor_info': {
                        'id': doctor.id,
                        'name': doctor.full_name,
                        'specialization': doctor.specialization.name if doctor.specialization else 'General'
                    },
                    'message': 'No appointments found for this doctor'
                })
            
            # Get unique patients from appointments
            patient_data = {}
            
            for appointment in doctor_appointments.select_related('patient', 'patient__user'):
                if hasattr(appointment, 'patient') and appointment.patient:
                    patient = appointment.patient
                    patient_id = patient.id
                    
                    if patient_id not in patient_data:
                        # Initialize patient data
                        patient_info = {
                            'id': patient_id,
                            'name': 'Unknown Patient',
                            'email': 'N/A',
                            'phone': 'N/A',
                            'age': None,
                            'gender': None,
                            'last_visit': None,
                            'total_appointments': 0,
                            'completed_appointments': 0,
                            'upcoming_appointments': 0,
                            'conditions': [],
                            'status': 'Active'
                        }
                        
                        # Get patient info from user if available
                        if hasattr(patient, 'user') and patient.user:
                            user = patient.user
                            patient_info.update({
                                'name': f"{user.first_name or ''} {user.last_name or ''}".strip() or 'Patient',
                                'email': user.email or 'N/A',
                                'phone': getattr(user, 'phone_number', 'N/A')
                            })
                        else:
                            # Try direct fields on patient
                            for field in ['full_name', 'name', 'email', 'phone_number', 'phone']:
                                if hasattr(patient, field):
                                    value = getattr(patient, field)
                                    if value:
                                        if field in ['full_name', 'name']:
                                            patient_info['name'] = value
                                        elif field == 'email':
                                            patient_info['email'] = value
                                        elif field in ['phone_number', 'phone']:
                                            patient_info['phone'] = value
                        
                        # Get additional patient fields if available
                        if hasattr(patient, 'age') and patient.age:
                            patient_info['age'] = patient.age
                        if hasattr(patient, 'gender') and patient.gender:
                            patient_info['gender'] = patient.gender
                        if hasattr(patient, 'date_of_birth') and patient.date_of_birth:
                            from datetime import date
                            today = date.today()
                            patient_info['age'] = today.year - patient.date_of_birth.year - ((today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day))
                        
                        patient_data[patient_id] = patient_info
                    
                    # Update appointment statistics
                    patient_data[patient_id]['total_appointments'] += 1
                    
                    if hasattr(appointment, 'status'):
                        if appointment.status == 'completed':
                            patient_data[patient_id]['completed_appointments'] += 1
                        elif appointment.status in ['scheduled', 'confirmed', 'pending']:
                            patient_data[patient_id]['upcoming_appointments'] += 1
                    
                    # Update last visit date
                    if hasattr(appointment, 'appointment_date') and appointment.appointment_date:
                        if (patient_data[patient_id]['last_visit'] is None or 
                            appointment.appointment_date > patient_data[patient_id]['last_visit']):
                            patient_data[patient_id]['last_visit'] = appointment.appointment_date
                    
                    # Add conditions/reasons
                    if hasattr(appointment, 'reason') and appointment.reason:
                        if appointment.reason not in patient_data[patient_id]['conditions']:
                            patient_data[patient_id]['conditions'].append(appointment.reason)
            
            # Convert to list and apply search filter
            patients_list = list(patient_data.values())
            
            if search:
                patients_list = [
                    p for p in patients_list 
                    if (search.lower() in p['name'].lower() or 
                        any(search.lower() in condition.lower() for condition in p['conditions']) or
                        search.lower() in p['email'].lower())
                ]
            
            # Sort by last visit date (most recent first)
            patients_list.sort(key=lambda x: x['last_visit'] or '1900-01-01', reverse=True)
            
            # Format the response
            for patient in patients_list:
                if patient['last_visit']:
                    patient['last_visit'] = patient['last_visit'].isoformat()
                patient['primary_condition'] = patient['conditions'][0] if patient['conditions'] else 'General consultation'
                
                # Determine status based on appointments
                if patient['upcoming_appointments'] > 0:
                    patient['status'] = 'Active'
                elif patient['completed_appointments'] > 0:
                    patient['status'] = 'Follow-up available'
                else:
                    patient['status'] = 'Inactive'
            
            response_data = {
                'count': len(patients_list),
                'results': patients_list,
                'doctor_info': {
                    'id': doctor.id,
                    'name': doctor.full_name,
                    'specialization': doctor.specialization.name if doctor.specialization else 'General'
                },
                'statistics': {
                    'total_patients': len(patients_list),
                    'active_patients': len([p for p in patients_list if p['status'] == 'Active']),
                    'total_appointments': sum(p['total_appointments'] for p in patients_list),
                    'completed_appointments': sum(p['completed_appointments'] for p in patients_list),
                    'upcoming_appointments': sum(p['upcoming_appointments'] for p in patients_list)
                }
            }
            
            logger.info(
                f"Successfully returned {len(patients_list)} patients for doctor {doctor.id}"
            )
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(
                f"Error in DoctorPatientsView: {str(e)}",
                exc_info=True,
                extra={
                    'doctor_id': doctor.id,
                    'user_id': request.user.id
                }
            )
            return Response(
                {
                    'error': 'Failed to load patients',
                    'detail': str(e) if settings.DEBUG else 'Internal server error',
                    'doctor_info': {
                        'id': doctor.id,
                        'name': doctor.full_name,
                        'specialization': doctor.specialization.name if doctor.specialization else 'General'
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def is_doctor(self, user):
        """Check if user is a doctor"""
        if hasattr(user, 'role'):
            role = user.role
            if isinstance(role, str):
                return role.upper() == 'DOCTOR'
            return role == 'DOCTOR' or str(role).upper() == 'DOCTOR'
        return False