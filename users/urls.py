from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from . import views
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .serializers import CustomTokenObtainPairView

@api_view(['GET'])
@permission_classes([AllowAny]) 
def auth_root(request):
    """List available authentication endpoints"""
    base_url = request.build_absolute_uri('/')[:-1]  
    routes = {
        'jwt_token_obtain': f'{base_url}/api/auth/token/',
        'jwt_token_refresh': f'{base_url}/api/auth/token/refresh/',
        'jwt_token_verify': f'{base_url}/api/auth/token/verify/',
        'login_session': f'{base_url}/api/auth/login/',
        'register': f'{base_url}/api/auth/register/',
        'logout': f'{base_url}/api/auth/logout/',
        'profile': f'{base_url}/api/auth/profile/',
        'user_detail': f'{base_url}/api/auth/user/',
        'user_update': f'{base_url}/api/auth/user/update/',
        'change_password': f'{base_url}/api/auth/user/change-password/',
        'current_user': f'{base_url}/api/auth/current-user/',
        'test_auth': f'{base_url}/api/auth/test/',
        'create_test_users': f'{base_url}/api/auth/create-test-users/',
    
        'forgot_password': f'{base_url}/api/auth/password/forgot/',
        'verify_reset_code': f'{base_url}/api/auth/password/verify-code/',
        'reset_password': f'{base_url}/api/auth/password/reset/',
    }
    return Response(routes)

urlpatterns = [
    # Root endpoint - lists all available auth endpoints
    path('', auth_root, name='auth-root'),
    
    # JWT Authentication (for React frontend)
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Session Authentication (alternative - for Django templates)
    path('login/', views.LoginView.as_view(), name='login_session'),
    
    # User Management
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('user/', views.UserDetailView.as_view(), name='user_detail'),
    path('user/update/', views.UserUpdateView.as_view(), name='user_update'),
    path('user/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('current-user/', views.GetCurrentUserView.as_view(), name='current_user'),
    
    # Password Reset Endpoints - ADD THESE!
    path('password/forgot/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('password/verify-code/', views.VerifyResetCodeView.as_view(), name='verify_reset_code'),
    path('password/reset/', views.ResetPasswordView.as_view(), name='reset_password'),
    
    # ADMIN USER MANAGEMENT ENDPOINTS
    path('admin/users/', views.AdminUserListView.as_view(), name='admin-users-list'),
    path('admin/users/<int:id>/', views.AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/users/<int:id>/update-status/', views.AdminUpdateUserStatusView.as_view(), name='admin-user-update-status'),
    path('admin/users/bulk-delete/', views.AdminBulkDeleteUsersView.as_view(), name='admin-users-bulk-delete'),
    path('admin/users/export/', views.AdminExportUsersView.as_view(), name='admin-users-export'),
    
    # Test endpoints
    path('test/', views.TestAuthView.as_view(), name='test_auth'),
    path('create-test-users/', views.CreateTestUserView.as_view(), name='create_test_users'),
]