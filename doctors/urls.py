from django.urls import path
from .views import (
    DoctorListView, DoctorDetailView, DoctorProfileView, DoctorCreateView,
    SpecializationListView, AvailableDoctorsView, DoctorsBySpecializationView,
    DoctorDashboardView, DoctorAppointmentsView, UserInfoDebugView, DoctorRegistrationView,
    DoctorDashboardDataView, DoctorPatientsView, doctor_stats, public_doctor_stats, health_check, public_test, debug_appointments
)
from .schedule_views import (
    DoctorScheduleListCreateView, DoctorScheduleDetailView, WeeklyScheduleView,
    BulkScheduleCreateView, ScheduleExceptionListCreateView, ScheduleExceptionDetailView,
    DoctorAvailabilityView, AvailableSlotsView, toggle_availability, schedule_summary
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    #DOCTOR AUTHENTICATION 
    path('auth/login/', TokenObtainPairView.as_view(), name='doctor-login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='doctor-token-refresh'),
    
    #DOCTOR REGISTRATION
    path('register/', DoctorRegistrationView.as_view(), name='doctor-register'),
    
    #DOCTOR CRUD OPERATIONS
    path('', DoctorListView.as_view(), name='doctor-list'),
    path('<int:pk>/', DoctorDetailView.as_view(), name='doctor-detail'),
    path('profile/', DoctorProfileView.as_view(), name='doctor-profile'),
    path('create/', DoctorCreateView.as_view(), name='doctor-create'),
    
    #SPECIALIZATIONS
    path('specializations/', SpecializationListView.as_view(), name='specialization-list'),
    
    #FILTERED DOCTOR VIEWS
    path('available/', AvailableDoctorsView.as_view(), name='available-doctors'),
    path('specialization/<int:specialization_id>/', 
         DoctorsBySpecializationView.as_view(), name='doctors-by-specialization'),
    
    #DOCTOR-SPECIFIC FEATURE
    path('dashboard/', DoctorDashboardView.as_view(), name='doctor-dashboard'),
    path('appointments/', DoctorAppointmentsView.as_view(), name='doctor-appointments'),
    path('dashboard/data/', DoctorDashboardDataView.as_view(), name='doctor-dashboard-data'),
    path('patients/', DoctorPatientsView.as_view(), name='doctor-patients'),
    
    # DOCTOR SCHEDULE MANAGEMENT
    path('schedule/', DoctorScheduleListCreateView.as_view(), name='doctor-schedule-list'),
    path('schedule/<int:pk>/', DoctorScheduleDetailView.as_view(), name='doctor-schedule-detail'),
    path('schedule/weekly/', WeeklyScheduleView.as_view(), name='doctor-weekly-schedule'),
    path('schedule/bulk-create/', BulkScheduleCreateView.as_view(), name='doctor-schedule-bulk-create'),
    path('schedule/exceptions/', ScheduleExceptionListCreateView.as_view(), name='doctor-schedule-exceptions'),
    path('schedule/exceptions/<int:pk>/', ScheduleExceptionDetailView.as_view(), name='doctor-schedule-exception-detail'),
    path('schedule/availability/', DoctorAvailabilityView.as_view(), name='doctor-availability'),
    path('schedule/available-slots/', AvailableSlotsView.as_view(), name='doctor-available-slots'),
    path('schedule/toggle-availability/', toggle_availability, name='doctor-toggle-availability'),
    path('schedule/summary/', schedule_summary, name='doctor-schedule-summary'),
    
    #ADMIN/STATISTICS 
    path('stats/', doctor_stats, name='doctor-stats'),
    path('public-stats/', public_doctor_stats, name='public-doctor-stats'),
    
    #DEBUG/TESTING ENDPOINTS
    path('debug/info/', UserInfoDebugView.as_view(), name='user-debug'),
    path('debug/appointments/', debug_appointments, name='debug-appointments'),
    path('health/', health_check, name='health-check'),
    path('public-test/', public_test, name='public-test'),
]