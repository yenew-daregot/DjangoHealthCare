# config/urls/api_urls.py
from django.urls import path, include

# api/' prefix since it's already added in __init__.py
urlpatterns = [
    path('patients/', include('patients.urls')),
    path('doctors/', include('doctors.urls')),
    path('appointments/', include('appointments.urls')),
    path('prescriptions/', include('prescriptions.urls')),
    path('medical-records/', include('medical_records.urls')),
    path('labs/', include('labs.urls')),
    path('emergency/', include('emergency.urls')),
    path('billing/', include('billing.urls')),
    path('chat/', include('chat.urls')),
    path('notifications/', include('notifications.urls')),
    path('medicationManagment/', include('medicationManagment.urls')),
]