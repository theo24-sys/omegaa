from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatsession',
            name='interview_active_until',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
