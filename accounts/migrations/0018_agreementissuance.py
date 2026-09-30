from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_alter_customuser_didit_verification_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='AgreementIssuance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agreement_id', models.CharField(max_length=20, unique=True, verbose_name='Agreement ID')),
                ('status', models.CharField(
                    choices=[('pending', 'Downloaded, awaiting signed copy'), ('submitted', 'Signed copy uploaded'), ('verified', 'Verified by admin')],
                    default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agreement_issuances', to='accounts.customuser')),
            ],
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'Agreement Issuance',
                'verbose_name_plural': 'Agreement Issuances',
            },
        ),
    ]
