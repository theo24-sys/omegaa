# Generated manually to add missing badge_appliance field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_customuser_police_clearance'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='badge_appliance',
            field=models.BooleanField(default=False, verbose_name='Appliance Certified'),
        ),
    ]
