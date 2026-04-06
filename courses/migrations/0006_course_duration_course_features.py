# Generated manually for the Charlady Academy update

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0005_coursecompletion_certificate'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='duration',
            field=models.CharField(blank=True, help_text='e.g. 1 week, 2-3 weeks', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='features',
            field=models.TextField(blank=True, help_text='Comma-separated or bullet-point features', null=True),
        ),
    ]
