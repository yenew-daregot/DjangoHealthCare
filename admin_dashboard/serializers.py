from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from patients.models import Patient
from doctors.models import Doctor

User = get_user_model()

class AdminCreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'phone_number', 'address'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        print("=" * 30)
        print("AdminCreateUserSerializer.create()")
        print(f"Validated data: {validated_data}")
        
        # Remove confirm_password from validated data
        if 'confirm_password' in validated_data:
            validated_data.pop('confirm_password')
            print("✅ Removed confirm_password field")
        
        # Create user with hashed password
        try:
            user = User.objects.create_user(**validated_data)
            print(f"✅ User created successfully: {user.username}")
            return user
        except Exception as e:
            print(f"❌ Error creating user: {str(e)}")
            raise e


class AdminCreatePatientSerializer(serializers.ModelSerializer):
    user = AdminCreateUserSerializer()
    
    class Meta:
        model = Patient
        fields = [
            'user', 'age', 'gender', 'date_of_birth', 'blood_group',
            'height', 'weight', 'emergency_contact', 'emergency_contact_phone',
            'insurance_id', 'allergy_notes', 'chronic_conditions'
        ]
        extra_kwargs = {
            'age': {'required': False, 'allow_null': True},
            'gender': {'required': False, 'allow_null': True},
            'date_of_birth': {'required': False, 'allow_null': True},
            'height': {'required': False, 'allow_null': True},
            'weight': {'required': False, 'allow_null': True},
        }
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'PATIENT'
        
        # Create user
        user_serializer = AdminCreateUserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        
        # Create patient
        patient = Patient.objects.create(user=user, **validated_data)
        return patient


class AdminCreateDoctorSerializer(serializers.ModelSerializer):
    user = AdminCreateUserSerializer()
    
    class Meta:
        model = Doctor
        fields = [
            'user', 'specialization', 'license_number', 'qualification',
            'years_of_experience', 'consultation_fee', 'bio', 'address',
            'is_available', 'is_verified'
        ]
        extra_kwargs = {
            'is_available': {'default': True},
            'is_verified': {'default': True},
            'years_of_experience': {'required': False, 'allow_null': True},
            'consultation_fee': {'required': False, 'allow_null': True},
            'license_number': {'required': False},
            'qualification': {'required': False},
        }
    
    def validate(self, attrs):
        # Additional validation for doctor-specific fields
        if attrs.get('years_of_experience', 0) < 0:
            raise serializers.ValidationError({"years_of_experience": "Experience years cannot be negative."})
        
        if attrs.get('consultation_fee', 0) < 0:
            raise serializers.ValidationError({"consultation_fee": "Consultation fee cannot be negative."})
        
        return attrs
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'DOCTOR'
        
        # Create user
        user_serializer = AdminCreateUserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        
        # Handle specialization - if it's a string, try to find or create it
        specialization_data = validated_data.get('specialization')
        if specialization_data and isinstance(specialization_data, str):
            from doctors.models import Specialization
            specialization, created = Specialization.objects.get_or_create(
                name=specialization_data,
                defaults={'description': f'Specialization in {specialization_data}'}
            )
            validated_data['specialization'] = specialization
        
        # Set default values for required fields if not provided
        if 'license_number' not in validated_data or not validated_data['license_number']:
            validated_data['license_number'] = f"LIC{user.id:06d}"
        
        if 'qualification' not in validated_data or not validated_data['qualification']:
            validated_data['qualification'] = "MD"
        
        # Create doctor
        doctor = Doctor.objects.create(user=user, **validated_data)
        return doctor


class ReportRequestSerializer(serializers.Serializer):
    """Serializer for report generation requests"""
    report_type = serializers.ChoiceField(
        choices=[
            ('patients_summary', 'Patients Summary'),
            ('doctors_summary', 'Doctors Summary'),
            ('appointments_summary', 'Appointments Summary'),
            ('financial_summary', 'Financial Summary'),
        ]
    )
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    format = serializers.ChoiceField(
        choices=[('json', 'JSON'), ('csv', 'CSV'), ('pdf', 'PDF')],
        default='json'
    )