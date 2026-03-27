# # config/urls.py
# from django.contrib import admin
# from django.urls import path, include
# from django.conf import settings
# from django.conf.urls.static import static
# from django.http import JsonResponse
# from django.utils import timezone

# # Simple view functions
# def api_root(request):
#     return JsonResponse({
#         'status': 'Running', 
#         'message': 'Welcome to the Medical API backend.',
#         'timestamp': timezone.now().isoformat(),
#         'version': '1.0.0'
#     })

# def health_check(request):
#     return JsonResponse({
#         'status': 'healthy',
#         'service': 'Medical System API',
#         'timestamp': timezone.now().isoformat(),
#         'environment': 'development' if settings.DEBUG else 'production'
#     })

# def test_endpoint(request):
#     return JsonResponse({
#         'status': 'success',
#         'message': 'Django backend is connected!',
#         'timestamp': timezone.now().isoformat(),
#     })

# urlpatterns = [
#     # Admin - MUST be first
#     path('admin/', admin.site.urls),
    
#     # Root URL
#     path('', api_root, name='root'),
    
#     # Basic API URLs
#     path('api/', api_root, name='api-root'),
#     path('api/health/', health_check, name='health-check'),
#     path('api/test/', test_endpoint, name='test-connection'),
# ]

# # Add API endpoints if the apps exist
# try:
#     # Add patients API
#     urlpatterns += [
#         path('api/patients/', include('patients.urls')),
#     ]
# except ImportError:
#     print("Warning: patients app not found")

# try:
#     # Add other API endpoints
#     urlpatterns += [
#         path('api/doctors/', include('doctors.urls')),
#         path('api/appointments/', include('appointments.urls')),
#         path('api/auth/', include('users.urls')),
#         path('api/prescriptions/', include('prescriptions.urls')),
#         path('api/medical-records/', include('medical_records.urls')),
#         path('api/labs/', include('labs.urls')),
#         path('api/emergency/', include('emergency.urls')),
#         path('api/billing/', include('billing.urls')),
#         path('api/chat/', include('chat.urls')),
#         path('api/notifications/', include('notifications.urls')),
#         path('api/medicationManagment/', include('medicationManagment.urls')),
#         path('api/health/', include('health.urls')),
#         path('api/admin/', include('admin_dashboard.urls')),  
#     ]
# except ImportError as e:
#     print(f"Warning: Some API apps not found: {e}")

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# config/urls.py - CORRECTED VERSION
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

# Simple view functions
def api_root(request):
    return JsonResponse({
        'status': 'Running', 
        'message': 'Welcome to the Medical API backend.',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })

def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'service': 'Medical System API',
        'timestamp': timezone.now().isoformat(),
        'environment': 'development' if settings.DEBUG else 'production'
    })

def test_endpoint(request):
    return JsonResponse({
        'status': 'success',
        'message': 'Django backend is connected!',
        'timestamp': timezone.now().isoformat(),
    })

# Debug view to check all URLs
@csrf_exempt
def debug_urls(request):
    from django.urls import get_resolver
    resolver = get_resolver()
    
    urls_info = []
    for pattern in resolver.url_patterns:
        if hasattr(pattern, 'pattern'):
            urls_info.append({
                'pattern': str(pattern.pattern),
                'name': getattr(pattern, 'name', 'No name'),
                'callback': str(pattern.callback) if hasattr(pattern, 'callback') else 'N/A'
            })
    
    return JsonResponse({
        'total_urls': len(urls_info),
        'urls': urls_info[:20],  # First 20 URLs
        'auth_urls': [url for url in urls_info if 'auth' in str(url['pattern']).lower()]
    })

urlpatterns = [
    # Admin - MUST be first
    path('admin/', admin.site.urls),
    
    # Root URL
    path('', api_root, name='root'),
    
    # Basic API URLs
    path('api/', api_root, name='api-root'),
    path('api/health/', health_check, name='health-check'),
    path('api/test/', test_endpoint, name='test-connection'),
    
    # Debug endpoint
    path('api/debug/urls/', debug_urls, name='debug-urls'),
    
    #auth endpoint
    path('api/auth/', include('users.urls')),
]

# Patients API
urlpatterns += [
    path('api/patients/', include('patients.urls')),
]

# Other API endpoints
urlpatterns += [
    path('api/doctors/', include('doctors.urls')),
    path('api/appointments/', include('appointments.urls')),
    path('api/prescriptions/', include('prescriptions.urls')),
    path('api/medical-records/', include('medical_records.urls')),
    path('api/labs/', include('labs.urls')),
    path('api/emergency/', include('emergency.urls')),
    path('api/billing/', include('billing.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/medicationManagment/', include('medicationManagment.urls')), 
    path('api/health/', include('health.urls')),  
    path('api/admin-dashboard/', include('admin_dashboard.urls')),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)