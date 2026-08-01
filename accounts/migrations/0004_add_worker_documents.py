# Generated manually

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_customuser_managers'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='id_document',
            field=models.FileField(blank=True, help_text='ID document (ID/Passport)', null=True, upload_to='worker_docs/%Y/%m/%d/'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='agreement_form',
            field=models.FileField(blank=True, help_text='Signed agreement form', null=True, upload_to='worker_docs/%Y/%m/%d/'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='police_clearance',
            field=models.FileField(blank=True, help_text='Police clearance certificate', null=True, upload_to='worker_docs/%Y/%m/%d/'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='documents_verified',
            field=models.BooleanField(default=False, help_text='Admin has verified all documents'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='documents_verified_at',
            field=models.DateTimeField(blank=True, help_text='When admin verified docs (files purged 24h after this)', null=True),
        ),
    ]
