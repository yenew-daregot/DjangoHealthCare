# Generated migration for FCM token field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_add_laboratorist_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='fcm_token',
            field=models.TextField(blank=True, help_text='Firebase Cloud Messaging token for push notifications'),
        ),
    ]