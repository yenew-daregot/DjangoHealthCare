from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'records', views.MedicalRecordViewSet, basename='medicalrecord')
router.register(r'allergies', views.AllergyViewSet, basename='allergy')
router.register(r'diagnoses', views.DiagnosisViewSet, basename='diagnosis')
router.register(r'medications', views.MedicationHistoryViewSet, basename='medicationhistory')
router.register(r'vital-signs', views.VitalSignsRecordViewSet, basename='vitalsignsrecord')
router.register(r'immunizations', views.ImmunizationRecordViewSet, basename='immunizationrecord')

urlpatterns = [
    path('', include(router.urls)),
    
    # Additional endpoints
    path('patient/<int:patient_id>/summary/', views.PatientSummaryView.as_view(), name='patient-summary'),
    path('patient/<int:patient_id>/timeline/', views.PatientTimelineView.as_view(), name='patient-timeline'),
    path('reports/health-overview/', views.HealthOverviewView.as_view(), name='health-overview'),
    path('records/upload-file/', views.FileUploadView.as_view(), name='file-upload'),
]