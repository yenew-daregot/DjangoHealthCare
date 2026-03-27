from django.urls import path
from . import views

urlpatterns = [
    # CRUD operations
    path('', views.PatientListCreateView.as_view(), name='patient-list-create'),
    path('<int:pk>/', views.PatientDetailView.as_view(), name='patient-detail'),
    
    # User-specific operations
    path('profile/create/', views.PatientProfileCreateView.as_view(), name='patient-profile-create'),
    path('profile/', views.PatientProfileView.as_view(), name='patient-profile'),
    
    path('stats/', views.PatientStatsView.as_view(), name='patient-stats'),
    path('search/', views.PatientSearchView.as_view(), name='patient-search'),
    
]