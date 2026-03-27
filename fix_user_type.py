#!/usr/bin/env python
"""
Script to fix user_type references to role in emergency views
"""

import re

def fix_user_type_references():
    file_path = 'emergency/views.py'
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace user_type with role and adjust values
    replacements = [
        (r"user\.user_type == 'patient'", "user.role == 'PATIENT'"),
        (r"user\.user_type in \['doctor', 'admin'\]", "user.role in ['DOCTOR', 'ADMIN']"),
        (r"request\.user\.user_type == 'patient'", "request.user.role == 'PATIENT'"),
        (r"request\.user\.user_type in \['doctor', 'admin'\]", "request.user.role in ['DOCTOR', 'ADMIN']"),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Write the file back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed user_type references in emergency/views.py")

if __name__ == '__main__':
    fix_user_type_references()