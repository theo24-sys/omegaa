"""
Migration to add unique constraints and optimize payments
Note: The unique_together constraint on PaymentPlan is added in a separate migration
after duplicate data is removed.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),  # Adjust to your last migration
    ]

    operations = [
        # Add unique constraint to mpesa_transaction_id
        migrations.AlterField(
            model_name='payment',
            name='mpesa_transaction_id',
            field=models.CharField(
                blank=True,
                help_text='M-Pesa MpesaReceiptNumber from callback - UNIQUE to prevent duplicates',
                max_length=100,
                null=True,
                unique=True,
            ),
        ),
        # NOTE: unique_together for PaymentPlan is added in 0012_add_paymentplan_unique_constraint
        # after duplicate data is removed in 0011_remove_duplicate_payment_plans
    ]
