#!/usr/bin/env python
"""
Simple script to create lab migration files manually
"""
import os
from datetime import datetime

def create_migration_files():
    print("Creating lab migration files manually...")
    
    # Create migrations directory if it doesn't exist
    migrations_dir = "labs/migrations"
    os.makedirs(migrations_dir, exist_ok=True)
    
    # Create __init__.py if it doesn't exist
    init_file = os.path.join(migrations_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write("")
    
    # Get timestamp for migration file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    # Create users migration for LABORATORIST role
    users_migration_content = f'''# Generated manually for LABORATORIST role
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),  # Adjust based on your last migration
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(
                choices=[
                    ('PATIENT', 'Patient'),
                    ('DOCTOR', 'Doctor'),
                    ('LABORATORIST', 'Laboratorist'),
                    ('ADMIN', 'Admin')
                ],
                default='PATIENT',
                max_length=20
            ),
        ),
    ]
'''
    
    # Create labs migration
    labs_migration_content = f'''# Generated manually for lab models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('patients', '0001_initial'),
        ('doctors', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LabTest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('normal_range', models.TextField(blank=True)),
                ('price', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('category', models.CharField(blank=True, max_length=100)),
                ('sample_type', models.CharField(blank=True, max_length=100)),
                ('preparation_instructions', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='LabRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requested_date', models.DateTimeField(auto_now_add=True)),
                ('assigned_date', models.DateTimeField(blank=True, null=True)),
                ('sample_collected_date', models.DateTimeField(blank=True, null=True)),
                ('completed_date', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('requested', 'Requested'), ('assigned', 'Assigned to Lab'), ('sample_collected', 'Sample Collected'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='requested', max_length=20)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')], default='normal', max_length=10)),
                ('clinical_notes', models.TextField(blank=True, help_text="Doctor's clinical notes")),
                ('lab_notes', models.TextField(blank=True, help_text="Laboratorist's notes")),
                ('request_document', models.FileField(blank=True, null=True, upload_to='lab_requests/')),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='doctors.doctor')),
                ('laboratorist', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='patients.patient')),
                ('test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='labs.labtest')),
            ],
        ),
        migrations.CreateModel(
            name='LabResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result_text', models.TextField(blank=True)),
                ('result_document', models.FileField(blank=True, null=True, upload_to='lab_results/')),
                ('result_values', models.JSONField(blank=True, default=dict)),
                ('interpretation', models.TextField(blank=True)),
                ('is_abnormal', models.BooleanField(default=False)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('lab_request', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='result', to='labs.labrequest')),
            ],
        ),
    ]
'''
    
    # Write users migration
    users_migration_file = f"users/migrations/{timestamp}_add_laboratorist_role.py"
    try:
        with open(users_migration_file, 'w') as f:
            f.write(users_migration_content)
        print(f"✅ Created users migration: {users_migration_file}")
    except Exception as e:
        print(f"❌ Failed to create users migration: {e}")
    
    # Write labs migration
    labs_migration_file = f"labs/migrations/{timestamp}_initial.py"
    try:
        with open(labs_migration_file, 'w') as f:
            f.write(labs_migration_content)
        print(f"✅ Created labs migration: {labs_migration_file}")
    except Exception as e:
        print(f"❌ Failed to create labs migration: {e}")
    
    print("\n📋 Next steps:")
    print("1. Install missing dependencies: pip install drf-yasg django-filter")
    print("2. Run: python manage.py migrate")
    print("3. Test the lab system with: python test_lab_system.py")

if __name__ == '__main__':
    create_migration_files()