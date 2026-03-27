# notifications/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .notification_views import (
    NotificationViewSet, 
    NotificationPreferenceViewSet,
    test_notification,  
    send_health_alert,  
    test_doctor_notification  
)
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'preferences', NotificationPreferenceViewSet, basename='notification-preference')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Enhanced notification endpoints 
    path('send/', NotificationViewSet.as_view({'post': 'send'}), name='send-notification'),
    path('history/', NotificationViewSet.as_view({'get': 'history'}), name='notification-history'),
    path('mark-all-read/', NotificationViewSet.as_view({'post': 'mark_all_read'}), name='mark-all-read'),
    path('unread-count/', NotificationViewSet.as_view({'get': 'unread_count'}), name='unread-count'),
    path('clear-old/', NotificationViewSet.as_view({'delete': 'clear_old'}), name='clear-old-notifications'),
    
    # Preference endpoints
    path('preferences/', NotificationPreferenceViewSet.as_view({'get': 'preferences'}), name='get-preferences'),
    path('preferences/update/', NotificationPreferenceViewSet.as_view({'put': 'update_preferences'}), name='update-preferences'),
    path('update-fcm-token/', NotificationPreferenceViewSet.as_view({'post': 'update_fcm_token'}), name='update-fcm-token'),
    path('service-status/', NotificationPreferenceViewSet.as_view({'get': 'service_status'}), name='service-status'),
    
    # Specialized notification endpoints 
    path('test/', test_notification, name='test-notification'),
    path('test-doctor/', test_doctor_notification, name='test-doctor-notification'),
    path('health-alert/', send_health_alert, name='send-health-alert'),
    path('send-appointment/', views.send_appointment_notification_view, name='send-appointment-notification'),
    
    path('doctor-preferences/<int:doctor_id>/', 
         views.get_doctor_notification_preferences,  
         name='doctor-preferences'),
    
    # Legacy endpoints 
    path('legacy/', views.NotificationListView.as_view(), name='notification-list'),
    path('legacy/<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('legacy/<int:pk>/mark-read/', views.MarkNotificationReadView.as_view(), name='mark-notification-read'),
    path('legacy/mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark-all-notifications-read'),
    path('legacy/unread-count/', views.UnreadNotificationCountView.as_view(), name='unread-notification-count'),
    path('legacy/recent/', views.RecentNotificationsView.as_view(), name='recent-notifications'),
    
    # Notification Preferences (legacy)
    path('legacy/preferences/', views.NotificationPreferenceView.as_view(), name='notification-preferences'),
    path('legacy/preferences/update/', views.UpdateNotificationPreferenceView.as_view(), name='update-notification-preferences'),
    
    # Templates
    path('templates/', views.NotificationTemplateListView.as_view(), name='notification-template-list'),
    path('templates/<int:pk>/', views.NotificationTemplateDetailView.as_view(), name='notification-template-detail'),
    
    # Bulk Notifications
    path('bulk/', views.BulkNotificationListCreateView.as_view(), name='bulk-notification-list'),
    path('bulk/<int:pk>/', views.BulkNotificationDetailView.as_view(), name='bulk-notification-detail'),
    path('bulk/<int:pk>/send/', views.SendBulkNotificationView.as_view(), name='send-bulk-notification'),
    
    # Scheduled Reminders
    path('reminders/', views.ScheduledReminderListCreateView.as_view(), name='scheduled-reminder-list'),
    path('reminders/<int:pk>/', views.ScheduledReminderDetailView.as_view(), name='scheduled-reminder-detail'),
    path('reminders/<int:pk>/toggle/', views.ToggleReminderView.as_view(), name='toggle-reminder'),
    
    # Analytics
    path('analytics/daily/', views.DailyNotificationAnalyticsView.as_view(), name='daily-notification-analytics'),
    path('analytics/summary/', views.NotificationSummaryView.as_view(), name='notification-summary'),
    
    # Mobile-specific endpoints
    path('mobile/register-device/', views.RegisterMobileDeviceView.as_view(), name='register-mobile-device'),
    path('mobile/unregister-device/', views.UnregisterMobileDeviceView.as_view(), name='unregister-mobile-device'),
]