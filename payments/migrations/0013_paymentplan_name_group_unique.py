from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0012_add_paymentplan_unique_constraint'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='paymentplan',
            unique_together={('name', 'target_group')},
        ),
    ]