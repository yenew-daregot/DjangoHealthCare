# config/urls/admin_urls.py
from django.urls import path, include

urlpatterns = [
    path('admin/', include('admin_dashboard.urls')),
]