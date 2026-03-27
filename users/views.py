from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import CustomUser
from django.db.models import Q
from .serializers import UserSerializer, RegisterSerializer, UserLoginSerializer
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from datetime import datetime, timedelta
from django.http import HttpResponse
from rest_framework.permissions import IsAdminUser
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
import csv
from io import StringIO

#ADMIN USER MANAGEMENT VIEWS
class AdminUserListView(ListCreateAPIView):
    """Admin view for listing all users and creating new ones"""
    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer
    queryset = CustomUser.objects.all().order_by('-date_joined')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['role', 'is_active', 'is_staff', 'is_superuser']
    search_fields = [
        'username', 'email', 'first_name', 'last_name', 
        'phone_number', 'address'
    ]
    
    def get_serializer_class(self):
        """Use RegisterSerializer for POST (creation), UserSerializer for GET"""
        if self.request.method == 'POST':
            return RegisterSerializer
        return UserSerializer

class AdminUserDetailView(RetrieveUpdateDestroyAPIView):
    """Admin view for user details, update, and delete"""
    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer
    queryset = CustomUser.objects.all()
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Use appropriate serializer based on HTTP method"""
        if self.request.method in ['PUT', 'PATCH']:
            return UserSerializer  # Or create an AdminUserUpdateSerializer
        return UserSerializer

class AdminUpdateUserStatusView(APIView):
    """Admin view to update user status (is_active)"""
    permission_classes = [IsAdminUser]
    
    def patch(self, request, id):
        try:
            user = CustomUser.objects.get(id=id)
            data = request.data
            
            # Update is_active if provided
            if 'is_active' in data:
                user.is_active = data['is_active']
            
            # Update role if provided
            if 'role' in data and data['role'] in ['PATIENT', 'DOCTOR', 'ADMIN']:
                user.role = data['role']
                # Ensure ADMIN users have is_staff=True
                if data['role'] == 'ADMIN':
                    user.is_staff = True
                    user.is_superuser = True
            
            user.save()
            return Response(UserSerializer(user).data)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

class AdminBulkDeleteUsersView(APIView):
    """Admin view for bulk user deletion"""
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        user_ids = request.data.get('ids', [])
        if not user_ids:
            return Response({'error': 'No user IDs provided'}, status=400)
        
        # Prevent admin from deleting themselves
        if request.user.id in user_ids:
            return Response({'error': 'Cannot delete yourself'}, status=400)
        
        # Get users that exist
        users = CustomUser.objects.filter(id__in=user_ids)
        deleted_count = users.count()
        
        # Delete users
        users.delete()
        
        return Response({
            'message': f'{deleted_count} users deleted successfully',
            'deleted_count': deleted_count
        })

class AdminExportUsersView(APIView):
    """Admin view to export users as CSV"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        # Get filter parameters
        role = request.GET.get('role')
        status = request.GET.get('status')
        search = request.GET.get('search')
        
        # Filter users
        users = CustomUser.objects.all()
        
        if role and role != 'all':
            users = users.filter(role=role)
        
        if status and status != 'all':
            if status == 'active':
                users = users.filter(is_active=True)
            elif status == 'inactive':
                users = users.filter(is_active=False)
        
        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone_number__icontains=search)
            )
        
        # Create CSV
        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer)
        
        # Write headers
        csv_writer.writerow([
            'ID', 'Username', 'Email', 'First Name', 'Last Name',
            'Role', 'Phone', 'Date Joined', 'Last Login',
            'Status', 'Is Staff', 'Is Superuser', 'Address'
        ])
        
        # Write data rows
        for user in users:
            csv_writer.writerow([
                user.id,
                user.username,
                user.email,
                user.first_name or '',
                user.last_name or '',
                user.role,
                user.phone_number or '',
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if user.date_joined else '',
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
                'Active' if user.is_active else 'Inactive',
                'Yes' if user.is_staff else 'No',
                'Yes' if user.is_superuser else 'No',
                user.address or ''
            ])
        
        # Create HTTP response
        response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="users_export_{timestamp}.csv"'
        return response

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        print("=" * 50)
        print("REGISTRATION REQUEST")
        print("Raw request data:", request.data)
        print("Data type:", type(request.data))
        
        #Print all keys in request.data
        if hasattr(request.data, 'keys'):
            print("Keys in request.data:", list(request.data.keys()))
        
        serializer = RegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            print("✅ Serializer is valid")
            print("Validated data:", serializer.validated_data)
            
            try:
                # Create user
                user = serializer.save()
                print(f"✅ User created: {user.username}")
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                print(f"❌ Error creating user: {str(e)}")
                import traceback
                traceback.print_exc()
                return Response({
                    'error': 'Registration failed',
                    'detail': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            print("❌ Serializer errors:", serializer.errors)
            print("❌ Data that caused errors:", request.data)
        
        # Return validation errors
        return Response({
            'error': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    auth_login(request, user)
                    refresh = RefreshToken.for_user(user)
                    
                    return Response({
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        'user': UserSerializer(user).data
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': 'Account is disabled'
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            auth_logout(request)
            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class UserUpdateView(generics.UpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")
        
        # Validation
        if not old_password or not new_password or not confirm_password:
            return Response({
                'error': 'All fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.check_password(old_password):
            return Response({
                'error': 'Old password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirm_password:
            return Response({
                'error': 'New passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate new password
        try:
            validate_password(new_password, user)
        except DjangoValidationError as e:
            return Response({
                'error': ', '.join(e.messages)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update password
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Password updated successfully'
        }, status=status.HTTP_200_OK)

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

# Test endpoints
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User as AuthUser

class TestAuthView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'status': 'success',
            'message': 'Authentication test endpoint',
            'is_authenticated': request.user.is_authenticated,
            'user': str(request.user),
            'user_type': getattr(request.user, 'role', None) if request.user.is_authenticated else None
        })

class CreateTestUserView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            # Create test users if they don't exist
            test_users = [
                {
                    'username': 'admin', 
                    'password': 'admin123', 
                    'email': 'admin@medical.com', 
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'role': 'ADMIN',
                    'is_staff': True, 
                    'is_superuser': True
                },
                {
                    'username': 'doctor1', 
                    'password': 'doctor123', 
                    'email': 'doctor@medical.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'role': 'DOCTOR',
                    'is_staff': True
                },
                {
                    'username': 'patient1', 
                    'password': 'patient123', 
                    'email': 'patient@medical.com',
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'role': 'PATIENT'
                },
            ]
            
            created_users = []
            for user_data in test_users:
                username = user_data['username']
                if not CustomUser.objects.filter(username=username).exists():
                    # Remove role from user_data before passing to create_user
                    role = user_data.pop('role')
                    user = CustomUser.objects.create_user(**user_data)
                    user.role = role  # Set role after creating user
                    user.save()
                    created_users.append({
                        'username': username,
                        'role': role,
                        'email': user_data['email']
                    })
            
            return Response({
                'status': 'success',
                'message': f'Created {len(created_users)} users' if created_users else 'All test users already exist',
                'users': created_users
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class GetCurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'is_authenticated': True,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser
        })

class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({'error': 'Email is required'}, status=400)
        
        try:
            user = CustomUser.objects.get(email=email)
            
            # ✅ THIS IS WHERE get_random_string GOES!
            reset_code = get_random_string(length=6, allowed_chars='0123456789')
            
            user.reset_token = reset_code
            user.reset_token_created = datetime.now()
            user.save()
            
            # In production, send email here
            # send_mail(
            #     subject='Password Reset Code',
            #     message=f'Your password reset code is: {reset_code}',
            #     from_email='noreply@yourdomain.com',
            #     recipient_list=[email],
            # )
            
            print(f"Reset code for {email}: {reset_code}")
            
            return Response({
                'message': 'Reset code sent to your email',
                'code': reset_code  # Remove this in production
            })
            
        except CustomUser.DoesNotExist:
            return Response({'error': 'Email not found'}, status=404)


class VerifyResetCodeView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        
        if not email or not code:
            return Response({'error': 'Email and code are required'}, status=400)
        
        try:
            user = CustomUser.objects.get(email=email, reset_token=code)
            
            # Check if code is expired (50 minutes)
            if user.reset_token_created:
                time_diff = datetime.now(user.reset_token_created.tzinfo) - user.reset_token_created
                if time_diff > timedelta(minutes=50):  # 50 minutes timeout
                    return Response({'error': 'Reset code has expired'}, status=400)
            
            return Response({
                'message': 'Code verified successfully'
            })
            
        except CustomUser.DoesNotExist:
            return Response({'error': 'Invalid reset code'}, status=400)


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        # Validation
        if not all([email, code, new_password, confirm_password]):
            return Response({'error': 'All fields are required'}, status=400)
        
        if new_password != confirm_password:
            return Response({'error': 'Passwords do not match'}, status=400)
        
        try:
            # Validate password
            from django.contrib.auth.password_validation import validate_password
            from django.core.exceptions import ValidationError
            
            # Create a dummy user for password validation
            dummy_user = CustomUser(email=email)
            try:
                validate_password(new_password, dummy_user)
            except ValidationError as e:
                return Response({'error': ', '.join(e.messages)}, status=400)
            
            # Find user and verify code
            user = CustomUser.objects.get(email=email, reset_token=code)
            
            # Check if code is expired (50 minutes - same as VerifyResetCodeView)
            if user.reset_token_created:
                time_diff = datetime.now(user.reset_token_created.tzinfo) - user.reset_token_created
                if time_diff > timedelta(minutes=50):  # Use 50 minutes, not 10
                    return Response({'error': 'Reset code has expired'}, status=400)
            
            # Update password
            user.set_password(new_password)
            user.reset_token = None
            user.reset_token_created = None
            user.save()
            
            return Response({
                'message': 'Password reset successful'
            })
            
        except CustomUser.DoesNotExist:
            return Response({'error': 'Invalid reset code or email'}, status=400)