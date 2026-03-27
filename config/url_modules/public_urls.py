# config/urls/public_urls.py
from django.urls import path
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

@csrf_exempt
def api_root(request):
    return JsonResponse({
        'status': 'Running', 
        'message': 'Welcome to the Medical API backend.',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })

@csrf_exempt
def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'service': 'Medical System API',
        'timestamp': timezone.now().isoformat(),
        'environment': 'development' if settings.DEBUG else 'production'
    })

@csrf_exempt
def test_endpoint(request):
    return JsonResponse({
        'status': 'success',
        'message': 'Django backend is connected!',
        'timestamp': timezone.now().isoformat(),
    })

urlpatterns = [
    # Add a root pattern to handle empty path
    path('api/', api_root, name='api-root'),
    path('api/health/', health_check, name='health-check'),
    path('api/test/', test_endpoint, name='test-connection'),
    # Add root redirect or welcome page
    path('', api_root, name='root'),
]