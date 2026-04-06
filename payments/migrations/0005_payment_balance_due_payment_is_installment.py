# Generated manually for the Charlady Academy update

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_paymentplan_target_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='balance_due',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Remaining balance for installments', max_digits=10),
        ),
        migrations.AddField(
            model_name='payment',
            name='is_installment',
            field=models.BooleanField(default=False, help_text='Is this a partial payment?'),
        ),
    ]
