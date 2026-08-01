# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_add_worker_documents'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='skills',
            field=models.CharField(blank=True, help_text='Comma-separated skills (househelp)', max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='experience',
            field=models.TextField(blank=True, help_text='Experience description (househelp)', null=True),
        ),
    ]
