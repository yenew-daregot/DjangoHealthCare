#!/usr/bin/env python
"""
Test script to check if appointments model can be imported
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_appointments_import():
    """Test if appointments model can be imported"""
    print("🔍 Testing appointments model import...")
    
    try:
        from appointments.models import Appointment
        print("✅ Successfully imported Appointment model")
        
        # Test basic model operations
        print(f"📊 Appointment model fields: {[f.name for f in Appointment._meta.get_fields()]}")
        
        # Check if there are any appointments in the database
        appointment_count = Appointment.objects.count()
        print(f"📈 Total appointments in database: {appointment_count}")
        
        # Test if we can create a basic query
        recent_appointments = Appointment.objects.all()[:5]
        print(f"📋 Recent appointments query successful: {len(recent_appointments)} found")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import Appointment model: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing appointments: {e}")
        return False

def test_doctors_appointments_view():
    """Test if the doctors appointments view can access appointments"""
    print("\n🔍 Testing doctors appointments view...")
    
    try:
        from doctors.views import HAS_APPOINTMENTS
        print(f"📊 HAS_APPOINTMENTS flag: {HAS_APPOINTMENTS}")
        
        if HAS_APPOINTMENTS:
            print("✅ Doctors view can access appointments")
        else:
            print("❌ Doctors view cannot access appointments")
            
        return HAS_APPOINTMENTS
        
    except Exception as e:
        print(f"❌ Error testing doctors view: {e}")
        return False

def test_appointments_urls():
    """Test if appointments URLs are accessible"""
    print("\n🔍 Testing appointments URLs...")
    
    try:
        from django.urls import reverse
        from django.test import Client
        
        # Test basic appointments URL
        client = Client()
        
        # This should return 401/403 (unauthorized) but not 404 (not found)
        response = client.get('/api/appointments/')
        print(f"📊 Appointments endpoint status: {response.status_code}")
        
        if response.status_code == 404:
            print("❌ Appointments endpoint not found (404)")
            return False
        else:
            print("✅ Appointments endpoint exists (got auth error, which is expected)")
            return True
            
    except Exception as e:
        print(f"❌ Error testing appointments URLs: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Starting appointments system diagnostics...\n")
    
    # Run tests
    import_success = test_appointments_import()
    view_success = test_doctors_appointments_view()
    url_success = test_appointments_urls()
    
    print(f"\n📊 Test Results:")
    print(f"   Import Test: {'✅ PASS' if import_success else '❌ FAIL'}")
    print(f"   View Test: {'✅ PASS' if view_success else '❌ FAIL'}")
    print(f"   URL Test: {'✅ PASS' if url_success else '❌ FAIL'}")
    
    if all([import_success, view_success, url_success]):
        print("\n🎉 All tests passed! Appointments system should be working.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        
        if not import_success:
            print("💡 Suggestion: Run migrations - python manage.py migrate")
        if not view_success:
            print("💡 Suggestion: Check for circular imports in doctors/views.py")
        if not url_success:
            print("💡 Suggestion: Check URL configuration in config/urls.py")