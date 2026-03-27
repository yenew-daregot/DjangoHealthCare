# Generated manually to enhance lab models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('labs', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add new fields to LabTest
        migrations.AddField(
            model_name='labtest',
            name='category',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='labtest',
            name='sample_type',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='labtest',
            name='preparation_instructions',
            field=models.TextField(blank=True),
        ),
        
        # Add new fields to LabRequest
        migrations.AddField(
            model_name='labrequest',
            name='laboratorist',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='labrequest',
            name='assigned_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='labrequest',
            name='sample_collected_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='labrequest',
            name='priority',
            field=models.CharField(choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')], default='normal', max_length=10),
        ),
        migrations.AddField(
            model_name='labrequest',
            name='clinical_notes',
            field=models.TextField(blank=True, help_text="Doctor's clinical notes"),
        ),
        migrations.AddField(
            model_name='labrequest',
            name='lab_notes',
            field=models.TextField(blank=True, help_text="Laboratorist's notes"),
        ),
        migrations.AddField(
            model_name='labrequest',
            name='request_document',
            field=models.FileField(blank=True, null=True, upload_to='lab_requests/'),
        ),
        
        # Update status choices
        migrations.AlterField(
            model_name='labrequest',
            name='status',
            field=models.CharField(choices=[('requested', 'Requested'), ('assigned', 'Assigned to Lab'), ('sample_collected', 'Sample Collected'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='requested', max_length=20),
        ),
        
        # Remove old fields that we're replacing
        migrations.RemoveField(
            model_name='labrequest',
            name='notes',
        ),
        migrations.RemoveField(
            model_name='labrequest',
            name='result',
        ),
        migrations.RemoveField(
            model_name='labrequest',
            name='result_file',
        ),
        
        # Create LabResult model
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