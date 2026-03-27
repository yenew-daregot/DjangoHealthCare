# config/urls/utility_urls.py
from django.urls import path
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.urls import get_resolver

@csrf_exempt
def list_all_urls(request):
    """Debug endpoint to list all registered URLs"""
    resolver = get_resolver()
    url_list = []
    
    def extract_urls(urlpatterns, prefix=''):
        for pattern in urlpatterns:
            if hasattr(pattern, 'url_patterns'):
                extract_urls(pattern.url_patterns, prefix + str(pattern.pattern))
            else:
                url_list.append({
                    'pattern': prefix + str(pattern.pattern),
                    'name': getattr(pattern, 'name', 'No name'),
                    'callback': str(pattern.callback) if hasattr(pattern, 'callback') else 'No callback'
                })
    
    extract_urls(resolver.url_patterns)
    return JsonResponse({'urls': url_list})

@csrf_exempt
def server_info(request):
    """Get server information"""
    import platform
    import sys
    import django
    
    return JsonResponse({
        'python_version': platform.python_version(),
        'django_version': django.get_version(),
        'platform': platform.platform(),
        'server_time': timezone.now().isoformat(),
        'debug_mode': settings.DEBUG,
        'installed_apps': list(settings.INSTALLED_APPS),
        'database_backend': settings.DATABASES['default']['ENGINE'],
    })

urlpatterns = [
    path('debug/urls/', list_all_urls, name='debug-urls'),
    path('server-info/', server_info, name='server-info'),
]