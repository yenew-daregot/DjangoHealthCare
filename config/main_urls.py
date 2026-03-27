from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.utils import timezone

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

# Basic URL patterns - start with minimal configuration
urlpatterns = [
    # Django Admin - MUST be first
    path('admin/', admin.site.urls),
    
    # Root URL
    path('', api_root, name='root'),
    
    # Basic API URLs
    path('api/', api_root, name='api-root'),
    path('api/health/', health_check, name='health-check'),
    path('api/test/', test_endpoint, name='test-connection'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)