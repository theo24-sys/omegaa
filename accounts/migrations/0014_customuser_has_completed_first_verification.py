# Generated migration for first-time verification tracking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_customuser_didit_session_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='has_completed_first_verification',
            field=models.BooleanField(
                default=False,
                help_text='Whether the user has completed first-time Didit identity verification'
            ),
        ),
    ]
