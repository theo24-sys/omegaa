from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_payment_course_alter_payment_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentplan',
            name='target_group',
            field=models.CharField(choices=[('employer', 'Employer'), ('worker', 'Worker')], default='employer', max_length=20),
        ),
    ]
