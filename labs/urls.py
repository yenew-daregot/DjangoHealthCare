from django.urls import path
from . import views

urlpatterns = [
    # Lab requests
    path('requests/', views.LabRequestListCreateView.as_view(), name='lab-request-list'),
    path('requests/<int:pk>/', views.LabRequestDetailView.as_view(), name='lab-request-detail'),
    path('requests/<int:pk>/update-status/', views.UpdateLabRequestStatusView.as_view(), name='update-lab-status'),
    path('requests/<int:pk>/assign-laboratorist/', views.AssignLaboratoristView.as_view(), name='assign-laboratorist'),
    
    # Lab results
    path('requests/<int:lab_request_id>/result/', views.LabResultCreateUpdateView.as_view(), name='lab-result-create-update'),
    
    # Lab tests
    path('tests/', views.LabTestListView.as_view(), name='lab-test-list'),
    path('tests/<int:pk>/', views.LabTestDetailView.as_view(), name='lab-test-detail'),
    
    # User-specific views
    path('patient/<int:patient_id>/', views.PatientLabRequestsView.as_view(), name='patient-lab-requests'),
    path('doctor/<int:doctor_id>/', views.DoctorLabRequestsView.as_view(), name='doctor-lab-requests'),
    path('laboratorist/<int:laboratorist_id>/', views.LaboratoristLabRequestsView.as_view(), name='laboratorist-lab-requests'),
    
    # Utility endpoints
    path('laboratorists/', views.LaboratoristListView.as_view(), name='laboratorist-list'),
    path('search-users/', views.search_users, name='search-users'),
    path('dashboard-stats/', views.lab_dashboard_stats, name='lab-dashboard-stats'),
]