from rest_framework import serializers
import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Patient
from users.models import CustomUser
from users.serializers import UserSerializer
from decimal import Decimal  
from django.utils import timezone

class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    bmi = serializers.ReadOnlyField()
    bmi_category = serializers.ReadOnlyField()
    
    # Add user fields for updates
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    address = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = Patient
        fields = [
            'id', 'user', 'date_of_birth', 'age', 'gender', 'blood_group', 
            'height', 'weight', 'emergency_contact', 'emergency_contact_phone',
            'insurance_id', 'allergy_notes', 'chronic_conditions', 'created_at',
            'updated_at', 'bmi', 'bmi_category',
            # Add user fields for updates
            'first_name', 'last_name', 'email', 'phone', 'address'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'bmi', 'bmi_category']
        extra_kwargs = {
            'first_name': {'write_only': True},
            'last_name': {'write_only': True},
            'email': {'write_only': True},
            'phone': {'write_only': True},
            'address': {'write_only': True},
        }
    
    def validate_emergency_contact_phone(self, value):
        if value and not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError("Enter a valid phone number.")
        return value
    
    def update(self, instance, validated_data):
        # Extract user fields
        user_fields = {}
        patient_fields = {}
        
        # Handle nested user data (from frontend)
        if 'user' in validated_data:
            user_data = validated_data.pop('user')
            user_fields.update(user_data)
        
        # Separate user fields from patient fields
        for field, value in validated_data.items():
            if field in ['first_name', 'last_name', 'email', 'phone', 'address']:
                if field == 'phone':
                    user_fields['phone_number'] = value  # Map phone to phone_number
                else:
                    user_fields[field] = value
            else:
                patient_fields[field] = value
        
        # Update user fields if any
        if user_fields and instance.user:
            for field, value in user_fields.items():
                setattr(instance.user, field, value)
            instance.user.save()
        
        # Update patient fields
        patient = super().update(instance, patient_fields)
        
        return patient


class PatientCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating patient profiles with user data"""
    username = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(write_only=True, required=True)
    password = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'},
        min_length=8
    )
    confirm_password = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    address = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = Patient
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'phone', 'address',
            'date_of_birth', 'gender', 'blood_group', 'height', 'weight',
            'emergency_contact', 'emergency_contact_phone', 'insurance_id',
            'allergy_notes', 'chronic_conditions'
        ]
    
    def validate(self, attrs):
        # Check if passwords match
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        
        # Validate username uniqueness
        username = attrs.get('username')
        if username and CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError({
                'username': 'A user with this username already exists.'
            })
        
        # Validate email uniqueness
        email = attrs.get('email')
        if email and CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError({
                'email': 'A user with this email already exists.'
            })
        
        # Validate phone number format if provided
        phone = attrs.get('phone')
        if phone and not re.match(r'^\+?1?\d{9,15}$', phone):
            raise serializers.ValidationError({
                'phone': 'Enter a valid phone number.'
            })
        
        # Validate emergency contact phone if provided
        emergency_phone = attrs.get('emergency_contact_phone')
        if emergency_phone and not re.match(r'^\+?1?\d{9,15}$', emergency_phone):
            raise serializers.ValidationError({
                'emergency_contact_phone': 'Enter a valid emergency contact phone number.'
            })
        
        #Height and weight validation - convert to Decimal for comparison
        height = attrs.get('height')
        if height is not None:
            try:
                height_decimal = Decimal(str(height))
                if height_decimal < Decimal('50.0') or height_decimal > Decimal('250.0'):
                    raise serializers.ValidationError({
                        'height': 'Height must be between 50cm and 250cm.'
                    })
                attrs['height'] = height_decimal  
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'height': 'Height must be a valid number.'
                })
        
        weight = attrs.get('weight')
        if weight is not None:
            try:
                weight_decimal = Decimal(str(weight))
                if weight_decimal < Decimal('2.0') or weight_decimal > Decimal('300.0'):
                    raise serializers.ValidationError({
                        'weight': 'Weight must be between 2kg and 300kg.'
                    })
                attrs['weight'] = weight_decimal  
            except (ValueError, TypeError):
                raise serializers.ValidationError({
                    'weight': 'Weight must be a valid number.'
                })
        
        return attrs
    
    def create(self, validated_data):
        # Extract user data
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'password': validated_data.pop('password'),
            'role': 'PATIENT'  
        }
        
        # Remove confirm_password from validated_data
        validated_data.pop('confirm_password', None)
        
        # Add optional user fields
        optional_fields = ['first_name', 'last_name', 'phone', 'address']
        for field in optional_fields:
            if field in validated_data:
                user_data[field] = validated_data.pop(field)
        
        try:
            # Create user
            user = CustomUser.objects.create_user(**user_data)
            
            # Create patient profile
            patient = Patient.objects.create(user=user, **validated_data)
            return patient
            
        except Exception as e:
            # If patient creation fails, delete the user if it was created
            if 'user' in locals():
                user.delete()
            raise serializers.ValidationError(f"Failed to create patient: {str(e)}")

class PatientProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for existing users to create a patient profile."""
    class Meta:
        model = Patient
        fields = [
            'date_of_birth', 'gender', 'blood_group', 'height', 'weight',
            'emergency_contact', 'emergency_contact_phone', 'insurance_id',
            'allergy_notes', 'chronic_conditions'
        ]
        # All fields are optional except those you mark as required
        extra_kwargs = {
            'date_of_birth': {'required': True},
            'gender': {'required': True},
        }

    def validate(self, attrs):
        # Add any profile-specific validation here
        # For example, calculate age from date_of_birth
        if 'date_of_birth' in attrs:
            today = timezone.now().date()
            birth_date = attrs['date_of_birth']
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            attrs['age'] = age
        return attrs

    def create(self, validated_data):
        # The user is taken from the request context
        user = self.context['request'].user
        # Ensure the user doesn't already have a profile
        if hasattr(user, 'patient_profile'):
            raise serializers.ValidationError("User already has a patient profile.")
        # Create and return the patient profile
        return Patient.objects.create(user=user, **validated_data)            