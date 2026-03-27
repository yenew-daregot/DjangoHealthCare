# Generated manually to add LABORATORIST role

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_customuser_avatar_url'),
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