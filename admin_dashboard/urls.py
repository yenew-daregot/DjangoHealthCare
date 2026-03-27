from django.urls import path
from . import views
from appointments import views as appointment_views
from medicationManagment import views as medication_views
from emergency import views as emergency_views

urlpatterns = [
    # ===== Dashboard & Analytics =====
    path('dashboard-stats/', views.AdminDashboardStatsView.as_view(), name='admin-dashboard-stats'),
    path('analytics/', views.AdminAnalyticsView.as_view(), name='admin-analytics'),
    path('recent-activities/', views.AdminRecentActivitiesView.as_view(), name='admin-recent-activities'),
    path('pending-actions/', views.AdminPendingActionsView.as_view(), name='admin-pending-actions'),
    # ===== User Management =====
    path('create-patient/', views.AdminCreatePatientView.as_view(), name='admin-create-patient'),
    path('create-doctor/', views.AdminCreateDoctorView.as_view(), name='admin-create-doctor'),
    
    # ===== Appointment Management =====
    path('appointments/', appointment_views.AdminAppointmentListView.as_view(), name='admin-appointments'),
    path('appointments/<int:pk>/', appointment_views.AdminAppointmentDetailView.as_view(), name='admin-appointment-detail'),
    path('appointments/statistics/', appointment_views.AppointmentStatisticsView.as_view(), name='appointment-statistics'),
    path('appointments/<int:pk>/status/', appointment_views.UpdateAppointmentStatusView.as_view(), name='update-appointment-status'),
    path('appointments/<int:pk>/cancel/', appointment_views.CancelAppointmentView.as_view(), name='cancel-appointment'),
    path('appointments/create/', appointment_views.CreateAppointmentView.as_view(), name='create-appointment'),
    path('appointments/search/', appointment_views.SearchAppointmentsView.as_view(), name='search-appointments'),
    
    # ===== Medication Management =====
    path('medications/', medication_views.AdminMedicationListView.as_view(), name='admin-medications'),
    path('medications/create/', medication_views.AdminCreateMedicationView.as_view(), name='admin-create-medication'),
    path('medications/<int:pk>/', medication_views.AdminMedicationDetailView.as_view(), name='admin-medication-detail'),
    path('medications/<int:pk>/update/', medication_views.AdminUpdateMedicationView.as_view(), name='admin-update-medication'),
    path('medications/<int:pk>/delete/', medication_views.AdminDeleteMedicationView.as_view(), name='admin-delete-medication'),
    path('medications/<int:pk>/update-stock/', medication_views.AdminUpdateStockView.as_view(), name='admin-update-stock'),
    path('medications/search/', medication_views.AdminSearchMedicationsView.as_view(), name='admin-search-medications'),
    path('medications/statistics/', medication_views.AdminMedicationStatisticsView.as_view(), name='admin-medication-statistics'),
    path('medications/low-stock/', medication_views.AdminLowStockMedicationsView.as_view(), name='admin-low-stock-medications'),
    path('medications/expiring-soon/', medication_views.AdminExpiringMedicationsView.as_view(), name='admin-expiring-medications'),
    
    #Emergency Management 
    path('emergencies/', emergency_views.AdminEmergencyRequestListView.as_view(), name='admin-emergency-list'),
    path('statistics/', emergency_views.EmergencyStatisticsView.as_view(), name='admin-emergency-stats'),
    path('reports/export/', emergency_views.ExportEmergencyReportView.as_view(), name='admin-emergency-export'),
    path('emergency-requests/', emergency_views.AdminEmergencyRequestListView.as_view(), name='admin-emergency-requests'),
    path('emergency-requests/<int:pk>/', emergency_views.AdminEmergencyRequestDetailView.as_view(), name='admin-emergency-request-detail'),
    path('emergency-requests/<int:pk>/status/', emergency_views.AdminUpdateEmergencyStatusView.as_view(), name='admin-update-emergency-status'),
    path('emergency-requests/<int:pk>/assign-team/', emergency_views.AdminAssignTeamView.as_view(), name='admin-assign-team'),
    path('emergency-requests/<int:pk>/location/', emergency_views.AdminUpdateEmergencyLocationView.as_view(), name='admin-update-emergency-location'),
    path('emergency-statistics/', emergency_views.AdminEmergencyStatisticsView.as_view(), name='admin-emergency-statistics'),
    path('reports/emergency-export/', emergency_views.AdminEmergencyExportView.as_view(), name='admin-emergency-export'),
    
    # ===== System Management =====
    path('system-status/', views.SystemStatusView.as_view(), name='system-status'),
    
    # ===== Reports =====
    path('generate-report/', views.GenerateReportView.as_view(), name='generate-report'),
    
    # ===== Health Check =====
    path('health/', appointment_views.HealthCheckView.as_view(), name='health-check'),
]