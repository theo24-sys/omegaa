"""
Migration to add unique constraint on PaymentPlan (plan_type, target_group)
This runs AFTER duplicate data has been removed in 0011_remove_duplicate_payment_plans
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0011_remove_duplicate_payment_plans'),
    ]

    operations = [
        # Add unique_together constraint to PaymentPlan after duplicates are removed
        migrations.AlterUniqueTogether(
            name='paymentplan',
            unique_together={('plan_type', 'target_group')},
        ),
    ]
