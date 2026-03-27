#!/usr/bin/env python
import os
import sys
import subprocess

# Change to backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("Starting Django development server...")
print("Backend directory:", os.getcwd())

try:
    # Run the Django development server
    subprocess.run([
        sys.executable, 'manage.py', 'runserver', '127.0.0.1:8000'
    ], check=True)
except KeyboardInterrupt:
    print("\nServer stopped by user")
except subprocess.CalledProcessError as e:
    print(f"Error starting server: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")