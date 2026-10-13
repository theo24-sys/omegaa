from django.db import migrations, models


def remove_duplicate_pending_agreements(apps, schema_editor):
    AgreementIssuance = apps.get_model('accounts', 'AgreementIssuance')
    pending = AgreementIssuance.objects.filter(status='pending').order_by('-created_at', '-id')
    retained_users = set()
    duplicate_ids = []
    for issuance in pending:
        if issuance.user_id in retained_users:
            duplicate_ids.append(issuance.id)
        else:
            retained_users.add(issuance.user_id)
    if duplicate_ids:
        AgreementIssuance.objects.filter(id__in=duplicate_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0021_customuser_is_identity_verified'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_pending_agreements, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='agreementissuance',
            constraint=models.UniqueConstraint(
                condition=models.Q(status='pending'),
                fields=('user',),
                name='one_pending_agreement_per_user',
            ),
        ),
    ]