from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from . import views

@api_view(['GET'])
@permission_classes([AllowAny])
def emergency_root(request):
    """
    Emergency Management System API Root
    Comprehensive emergency response system for hospital management
    """
    base_url = request.build_absolute_uri('/api/emergency')
    
    endpoints = {
        "api": "Emergency Management System",
        "version": "1.0",
        "description": "Comprehensive emergency response and management system",
        "features": [
            "Emergency contact management",
            "Emergency request tracking",
            "Response team coordination",
            "Real-time emergency alerts",
            "Emergency protocols and guidelines",
            "Statistics and reporting",
            "Mobile app integration"
        ],
        
        "endpoints": {
            "emergency_contacts": {
                "list_create": f"{base_url}/contacts/",
                "retrieve_update_destroy": f"{base_url}/contacts/{{id}}/",
                "patient_contacts": f"{base_url}/contacts/patient/{{patient_id}}/",
                "set_primary": f"{base_url}/contacts/{{id}}/set-primary/",
            },
            
            "emergency_requests": {
                "list_create": f"{base_url}/requests/",
                "retrieve_update_destroy": f"{base_url}/requests/{{id}}/",
                "by_request_id": f"{base_url}/requests/{{request_id}}/by-id/",
                "patient_requests": f"{base_url}/requests/patient/{{patient_id}}/",
                "update_status": f"{base_url}/requests/{{id}}/update-status/",
                "assign_team": f"{base_url}/requests/{{id}}/assign-team/",
                "active_emergencies": f"{base_url}/requests/active/",
                "critical_emergencies": f"{base_url}/requests/critical/",
            },
            
            "emergency_responses": {
                "list_create": f"{base_url}/responses/",
                "retrieve_update_destroy": f"{base_url}/responses/{{id}}/",
                "request_responses": f"{base_url}/responses/request/{{request_id}}/",
            },
            
            "response_teams": {
                "list": f"{base_url}/response-teams/",
                "detail": f"{base_url}/response-teams/{{id}}/",
                "available_teams": f"{base_url}/response-teams/available/",
                "update_member_status": f"{base_url}/response-teams/{{id}}/update-status/",
            },
            
            "emergency_alerts": {
                "list_create": f"{base_url}/alerts/",
                "retrieve_update_destroy": f"{base_url}/alerts/{{id}}/",
                "patient_alerts": f"{base_url}/alerts/patient/{{patient_id}}/",
                "verify_alert": f"{base_url}/alerts/{{id}}/verify/",
                "sos_alert": f"{base_url}/alerts/sos/",
            },
            
            "emergency_protocols": {
                "list": f"{base_url}/protocols/",
                "detail": f"{base_url}/protocols/{{id}}/",
                "by_type": f"{base_url}/protocols/type/{{protocol_type}}/",
            },
            
            "statistics_reports": {
                "statistics": f"{base_url}/statistics/",
                "export_report": f"{base_url}/reports/export/",
                "daily_stats": f"{base_url}/statistics/daily/",
                "monthly_stats": f"{base_url}/statistics/monthly/",
                "response_time_report": f"{base_url}/statistics/response-time/",
                "emergency_type_report": f"{base_url}/statistics/type-report/",
            },
            
            "mobile_endpoints": {
                "quick_sos": f"{base_url}/mobile/quick-sos/",
                "nearby_hospitals": f"{base_url}/mobile/nearby-hospitals/",
                "emergency_guide": f"{base_url}/mobile/emergency-guide/",
            },
            
            "real_time_features": {
                "update_location": f"{base_url}/requests/{{id}}/update-location/",
                "update_vitals": f"{base_url}/requests/{{id}}/update-vitals/",
                "add_note": f"{base_url}/requests/{{id}}/add-note/",
            },
            
            "admin_endpoints": {
                "admin_requests_list": f"{base_url}/admin/requests/",
                "admin_request_detail": f"{base_url}/admin/requests/{{id}}/",
                "admin_update_status": f"{base_url}/admin/requests/{{id}}/update-status/",
                "admin_assign_team": f"{base_url}/admin/requests/{{id}}/assign-team/",
                "admin_update_location": f"{base_url}/admin/requests/{{id}}/update-location/",
                "admin_statistics": f"{base_url}/admin/statistics/",
                "admin_export": f"{base_url}/admin/export/",
            }
        },
        
        "authentication": {
            "required": "Yes, for most endpoints",
            "methods": ["JWT Bearer Token", "Session Authentication"],
            "get_token": "POST /api/auth/token/ with username and password",
            "refresh_token": "POST /api/auth/token/refresh/ with refresh token",
        },
        
        "quick_start": {
            "1_get_token": "POST /api/auth/token/ with credentials",
            "2_create_emergency": "POST /api/emergency/requests/ with emergency details",
            "3_track_emergency": "GET /api/emergency/requests/{id}/",
            "4_update_status": "PATCH /api/emergency/requests/{id}/update-status/",
        },
        
        "contact": {
            "support": "emergency-support@hospital.com",
            "emergency_hotline": "+1-800-EMERGENCY",
            "documentation": "https://docs.hospital-emergency-api.com",
        },
        
        "status_codes": {
            "200": "OK - Request successful",
            "201": "Created - Resource created",
            "400": "Bad Request - Invalid input",
            "401": "Unauthorized - Authentication required",
            "403": "Forbidden - Insufficient permissions",
            "404": "Not Found - Resource not found",
            "500": "Internal Server Error",
        }
    }
    
    return Response(endpoints)

urlpatterns = [
    # Root endpoint - must be first
    path('', emergency_root, name='emergency-root'),
    
    # EMERGENCY CONTACTS
    path('contacts/', views.EmergencyContactListCreateView.as_view(), name='emergencycontact-list'),
    path('contacts/<int:pk>/', views.EmergencyContactDetailView.as_view(), name='emergencycontact-detail'),
    path('contacts/patient/<int:patient_id>/', views.PatientEmergencyContactsView.as_view(), name='patient-emergency-contacts'),
    path('contacts/<int:pk>/set-primary/', views.SetPrimaryContactView.as_view(), name='set-primary-contact'),
    
    # EMERGENCY REQUESTS
    path('requests/', views.EmergencyRequestListCreateView.as_view(), name='emergencyrequest-list'),
    path('requests/<int:pk>/', views.EmergencyRequestDetailView.as_view(), name='emergencyrequest-detail'),
    path('requests/<str:request_id>/by-id/', views.EmergencyRequestByIDView.as_view(), name='emergency-request-by-id'),
    path('requests/patient/<int:patient_id>/', views.PatientEmergencyRequestsView.as_view(), name='patient-emergency-requests'),
    path('requests/<int:pk>/update-status/', views.UpdateEmergencyStatusView.as_view(), name='update-emergency-status'),
    path('requests/<int:pk>/assign-team/', views.AssignResponseTeamView.as_view(), name='assign-response-team'),
    path('requests/active/', views.ActiveEmergenciesView.as_view(), name='active-emergencies'),
    path('requests/critical/', views.CriticalEmergenciesView.as_view(), name='critical-emergencies'),
    
    # EMERGENCY RESPONSES
    path('responses/', views.EmergencyResponseListCreateView.as_view(), name='emergency-response-list'),
    path('responses/<int:pk>/', views.EmergencyResponseDetailView.as_view(), name='emergency-response-detail'),
    path('responses/request/<int:request_id>/', views.EmergencyRequestResponseView.as_view(), name='emergency-request-response'),
    
    # EMERGENCY RESPONSE TEAM
    path('response-teams/', views.EmergencyResponseTeamListView.as_view(), name='emergencyresponseteam-list'),
    path('response-teams/<int:pk>/', views.EmergencyResponseTeamDetailView.as_view(), name='emergencyresponseteam-detail'),
    path('response-teams/available/', views.AvailableResponseTeamView.as_view(), name='available-response-team'),
    path('response-teams/<int:pk>/update-status/', views.UpdateTeamMemberStatusView.as_view(), name='update-team-status'),
    
    # EMERGENCY ALERTS
    path('alerts/', views.EmergencyAlertListCreateView.as_view(), name='emergencyalert-list'),
    path('alerts/<int:pk>/', views.EmergencyAlertDetailView.as_view(), name='emergencyalert-detail'),
    path('alerts/patient/<int:patient_id>/', views.PatientEmergencyAlertsView.as_view(), name='patient-emergency-alerts'),
    path('alerts/<int:pk>/verify/', views.VerifyEmergencyAlertView.as_view(), name='verify-emergency-alert'),
    path('alerts/sos/', views.SOSAlertView.as_view(), name='sos-alert'),
    
    # EMERGENCY PROTOCOLS
    path('protocols/', views.EmergencyProtocolListView.as_view(), name='emergencyprotocol-list'),
    path('protocols/<int:pk>/', views.EmergencyProtocolDetailView.as_view(), name='emergencyprotocol-detail'),
    path('protocols/type/<str:protocol_type>/', views.ProtocolsByTypeView.as_view(), name='protocols-by-type'),
    
    # STATISTICS & REPORTS
    path('statistics/', views.EmergencyStatisticsView.as_view(), name='emergency-statistics'),
    path('reports/export/', views.ExportEmergencyReportView.as_view(), name='emergency-export'),
    path('statistics/daily/', views.DailyEmergencyStatsView.as_view(), name='daily-emergency-stats'),
    path('statistics/monthly/', views.MonthlyEmergencyStatsView.as_view(), name='monthly-emergency-stats'),
    path('statistics/response-time/', views.ResponseTimeReportView.as_view(), name='response-time-report'),
    path('statistics/type-report/', views.EmergencyTypeReportView.as_view(), name='emergency-type-report'),
    
    # MOBILE APP ENDPOINTS
    path('mobile/quick-sos/', views.QuickSOSView.as_view(), name='quick-sos'),
    path('mobile/nearby-hospitals/', views.NearbyHospitalsView.as_view(), name='nearby-hospitals'),
    path('mobile/nearby-hospitals-enhanced/', views.NearbyHospitalsEnhancedView.as_view(), name='nearby-hospitals-enhanced'),
    path('mobile/calculate-route/', views.CalculateEmergencyRouteView.as_view(), name='calculate-emergency-route'),
    path('mobile/emergency-guide/', views.EmergencyGuideView.as_view(), name='emergency-guide'),
    
    # REAL-TIME FEATURES
    path('requests/<int:pk>/update-location/', views.UpdateEmergencyLocationView.as_view(), name='update-emergency-location'),
    path('requests/<int:pk>/update-vitals/', views.UpdateEmergencyVitalsView.as_view(), name='update-emergency-vitals'),
    path('requests/<int:pk>/add-note/', views.AddEmergencyNoteView.as_view(), name='add-emergency-note'),
    path('requests/<int:pk>/navigation/', views.NavigationInstructionsView.as_view(), name='navigation-instructions'),
    path('requests/<int:pk>/eta/', views.RealTimeETAView.as_view(), name='real-time-eta'),
    
    # AMBULANCE TRACKING
    path('ambulances/<str:ambulance_id>/location/', views.UpdateAmbulanceLocationView.as_view(), name='update-ambulance-location'),
    
    # ADMIN ENDPOINTS 
    path('admin/requests/', views.AdminEmergencyRequestListView.as_view(), name='admin-emergency-request-list'),
    path('admin/requests/<int:pk>/', views.AdminEmergencyRequestDetailView.as_view(), name='admin-emergency-request-detail'),
    path('admin/requests/<int:pk>/update-status/', views.AdminUpdateEmergencyStatusView.as_view(), name='admin-update-emergency-status'),
    path('admin/requests/<int:pk>/assign-team/', views.AdminAssignTeamView.as_view(), name='admin-assign-team'),
    path('admin/requests/<int:pk>/update-location/', views.AdminUpdateEmergencyLocationView.as_view(), name='admin-update-emergency-location'),
    path('admin/statistics/', views.AdminEmergencyStatisticsView.as_view(), name='admin-emergency-statistics'),
    path('admin/export/', views.AdminEmergencyExportView.as_view(), name='admin-emergency-export'),
]