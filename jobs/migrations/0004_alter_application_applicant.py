# Fix limit_choices_to to match actual user_type value ('househelp' not 'housekeeper')

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0003_alter_application_options_alter_job_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='applicant',
            field=models.ForeignKey(
                limit_choices_to={'user_type': 'househelp'},
                on_delete=django.db.models.deletion.CASCADE,
                related_name='applications',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
