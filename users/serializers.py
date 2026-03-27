from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 
                 'phone_number', 'date_of_birth', 'address', 'profile_picture', 
                 'is_verified', 'created_at')
        read_only_fields = ('id', 'is_verified', 'created_at')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'},
        validators=[validate_password]  
    )
    confirmPassword = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'},
        label='Confirm Password'
        # NO source parameter!
    )
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'confirmPassword',
                 'first_name', 'last_name', 'role', 'phone_number')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'role': {'required': True},
        }
    
    def validate(self, attrs):
        print("=" * 50)
        print("✅ [SERIALIZER VALIDATE] Starting validation")
        print("Raw attrs:", attrs)
        
        # Check if passwords match
        password = attrs.get('password')
        confirm_password = attrs.get('confirmPassword')  
        
        print(f"Checking password match: {password} == {confirm_password}")
        
        if password and confirm_password and password != confirm_password:
            print("❌ Passwords don't match!")
            raise serializers.ValidationError({
                "confirmPassword": "Password fields didn't match."
            })
        print("✅ Passwords match!")
        
        # Check if email already exists
        email = attrs.get('email')
        if email and CustomUser.objects.filter(email=email).exists():
            print(f"❌ Email already exists: {email}")
            raise serializers.ValidationError({
                "email": "A user with this email already exists."
            })
        print(f"✅ Email is unique: {email}")
        
        # Check if username already exists
        username = attrs.get('username')
        if username and CustomUser.objects.filter(username=username).exists():
            print(f"❌ Username already exists: {username}")
            raise serializers.ValidationError({
                "username": "A user with this username already exists."
            })
        print(f"✅ Username is unique: {username}")
        
        print("✅ [SERIALIZER VALIDATE] Validation passed!")
        print("=" * 50)
        return attrs

    def create(self, validated_data):
        print("=" * 50)
        print("✅ [SERIALIZER CREATE] Creating user")
        print("Validated data:", validated_data)
        
        # Remove confirmPassword from validated data
        if 'confirmPassword' in validated_data:
            validated_data.pop('confirmPassword')
            print("✅ Removed confirmPassword field")
        
        # Extract password
        password = validated_data.pop('password')
        print(f"✅ Extracted password (hashed): {password[:10]}...")
        
        # Set default role if not provided
        if 'role' not in validated_data:
            validated_data['role'] = 'PATIENT'
            print("✅ Set default role to PATIENT")
        
        # Create user instance
        user = CustomUser(**validated_data)
        
        # Set password properly (hashes it)
        user.set_password(password)
        
        # Save user
        user.save()
        
        print(f"✅ User created successfully: {user.username}")
        print("User details:", {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        })
        print("=" * 50)
        
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if not username or not password:
            raise serializers.ValidationError("Both username and password are required.")
        
        return attrs

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add custom claims
        data['user'] = UserSerializer(self.user).data
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer