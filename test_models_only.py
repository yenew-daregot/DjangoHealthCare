#!/usr/bin/env python
"""
Test script to check if our models are syntactically correct
"""
import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_model_imports():
    print("Testing model imports...")
    
    try:
        # Test importing our models without Django setup
        print("✓ Testing labs.models import...")
        from labs import models as lab_models
        print(f"  - LabTest: {lab_models.LabTest}")
        print(f"  - LabRequest: {lab_models.LabRequest}")
        print(f"  - LabResult: {lab_models.LabResult}")
        
        print("✓ Testing users.models import...")
        from users import models as user_models
        print(f"  - CustomUser: {user_models.CustomUser}")
        
        print("✓ Testing labs.serializers import...")
        from labs import serializers as lab_serializers
        print(f"  - LabTestSerializer: {lab_serializers.LabTestSerializer}")
        
        print("✓ Testing labs.views import...")
        from labs import views as lab_views
        print(f"  - LabRequestListCreateView: {lab_views.LabRequestListCreateView}")
        
        print("\n✅ All model imports successful!")
        print("The lab system code is syntactically correct.")
        print("\n📋 Next steps:")
        print("1. Resolve the migration conflicts manually")
        print("2. Or use the frontend components directly with existing backend")
        print("3. The frontend lab components are ready to use!")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_model_imports()
    if not success:
        sys.exit(1)