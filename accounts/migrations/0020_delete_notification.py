from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0019_merge_0017_and_0018'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Notification',
        ),
    ]