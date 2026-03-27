import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
    print("✅ Django setup successful")
    
    from doctors.models import Doctor
    doctors = Doctor.objects.all()
    print(f"✅ Found {doctors.count()} doctors in database")
    
    available_doctors = doctors.filter(is_available=True, is_verified=True)
    print(f"✅ Found {available_doctors.count()} available and verified doctors")
    
    for doctor in available_doctors[:3]:
        print(f"   - {doctor.full_name} (ID: {doctor.id})")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()