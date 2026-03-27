try:
    from rest_framework import serializers
    print("✓ rest_framework import successful")
except ImportError as e:
    print(f"✗ rest_framework import failed: {e}")

try:
    from rest_framwork import serializers
    print("✗ rest_framwork import should fail but didn't")
except ImportError:
    print("✓ rest_framwork import correctly failed")