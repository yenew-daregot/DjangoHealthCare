from django.urls import path
from .views import (
    AppointmentListCreateView,
    AppointmentDetailView,
    DoctorAppointmentsView,
    PatientAppointmentsView,
    TodayAppointmentsView,
    UpcomingAppointmentsView,
    AvailableSlotsView,
    UpdateAppointmentStatusView,
    CancelAppointmentView,
    AppointmentStatisticsView,
    CreateAppointmentView,
    SearchAppointmentsView
)

urlpatterns = [
    path('', AppointmentListCreateView.as_view(), name='appointment-list'),
    path('<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
    path('doctor-appointments/', DoctorAppointmentsView.as_view(), name='doctor-appointments'),
    path('patients/<int:patient_id>/', PatientAppointmentsView.as_view(), name='patient-appointments'),
    path('today/', TodayAppointmentsView.as_view(), name='today-appointments'),
    path('upcoming/', UpcomingAppointmentsView.as_view(), name='upcoming-appointments'),
    path('doctors/<int:doctor_id>/slots/', AvailableSlotsView.as_view(), name='available-slots'),
    path('<int:pk>/status/', UpdateAppointmentStatusView.as_view(), name='update-status'),
    path('<int:pk>/cancel/', CancelAppointmentView.as_view(), name='cancel-appointment'),
    
    # Admin views from your appointments/view.py
    path('admin/', AppointmentListCreateView.as_view(), name='admin-appointment-list'),
    path('admin/<int:pk>/', AppointmentDetailView.as_view(), name='admin-appointment-detail'),
    path('statistics/', AppointmentStatisticsView.as_view(), name='appointment-statistics'),
    path('admin/create/', CreateAppointmentView.as_view(), name='create-appointment'),
    path('admin/search/', SearchAppointmentsView.as_view(), name='search-appointments'),
    
]