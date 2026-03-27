from django.urls import path
from . import views

urlpatterns = [
    # Root endpoint
    path('', views.prescription_root, name='prescription-root'),
    
    # Prescription endpoints
    path('prescriptions/', views.PrescriptionListCreateView.as_view(), name='prescription-list'),
    path('prescriptions/<int:pk>/', views.PrescriptionDetailView.as_view(), name='prescription-detail'),
    path('prescriptions/patient/<int:patient_id>/', views.PatientPrescriptionsView.as_view(), name='patient-prescriptions'),
    path('prescriptions/doctor/<int:doctor_id>/', views.DoctorPrescriptionsView.as_view(), name='doctor-prescriptions'),
    path('prescriptions/active/', views.ActivePrescriptionsView.as_view(), name='active-prescriptions'),
    path('prescriptions/expired/', views.ExpiredPrescriptionsView.as_view(), name='expired-prescriptions'),
    
    # Medication endpoints
    path('medications/', views.MedicationListCreateView.as_view(), name='medication-list'),
    path('medications/<int:pk>/', views.MedicationDetailView.as_view(), name='medication-detail'),
    
    # Refill endpoints
    path('refills/', views.PrescriptionRefillListCreateView.as_view(), name='refill-list'),
    path('refills/<int:pk>/', views.PrescriptionRefillDetailView.as_view(), name='refill-detail'),
    path('refills/<int:pk>/approve/', views.ApproveRefillView.as_view(), name='approve-refill'),
    path('refills/<int:pk>/deny/', views.DenyRefillView.as_view(), name='deny-refill'),
    
    # Dashboard endpoints
    path('dashboard/doctor/', views.DoctorDashboardView.as_view(), name='doctor-dashboard'),
    path('dashboard/patient/', views.PatientDashboardView.as_view(), name='patient-dashboard'),
    path('statistics/', views.PrescriptionStatisticsView.as_view(), name='prescription-statistics'),
]