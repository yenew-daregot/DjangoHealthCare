import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import chat.routing
import appointments.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Combine WebSocket URL patterns from all apps
websocket_urlpatterns = [
    *chat.routing.websocket_urlpatterns,
    *appointments.routing.websocket_urlpatterns,
]

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})