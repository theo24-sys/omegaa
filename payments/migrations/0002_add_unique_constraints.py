"""
Migration to add unique constraints and optimize payments
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
        # Add unique_together constraint to PaymentPlan
        migrations.AlterUniqueTogether(
            name='paymentplan',
            unique_together={('plan_type', 'target_group')},
        ),
    ]
