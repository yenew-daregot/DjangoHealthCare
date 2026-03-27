from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'vital-types', views.VitalTypeViewSet)
router.register(r'vitals', views.VitalReadingViewSet, basename='vitalreading')
router.register(r'alerts', views.HealthAlertViewSet, basename='healthalert')
router.register(r'summaries', views.PatientHealthSummaryViewSet, basename='patienthealthsummary')
router.register(r'reports', views.HealthReportViewSet, basename='healthreport')

urlpatterns = [
    path('', include(router.urls)),
    
    # Additional endpoints
    path('patients/<int:patient_id>/vitals/', 
         views.VitalReadingViewSet.as_view({'get': 'patient_vitals'}), 
         name='patient-vitals'),
    
    path('patients/<int:patient_id>/summary/', 
         views.PatientHealthSummaryViewSet.as_view({'get': 'patient_summary'}), 
         name='patient-health-summary'),
    
    path('stats/', 
         views.HealthReportViewSet.as_view({'get': 'system_stats'}), 
         name='health-stats'),
]