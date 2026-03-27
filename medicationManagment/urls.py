from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MedicationViewSet, MedicationDoseViewSet, MedicationReminderViewSet

router = DefaultRouter()
router.register(r'medications', MedicationViewSet, basename='medication')
router.register(r'medication-doses', MedicationDoseViewSet, basename='medication-dose')
router.register(r'medication-reminders', MedicationReminderViewSet, basename='medication-reminder')

urlpatterns = [
    path('', include(router.urls)),
]