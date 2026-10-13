from django.db import migrations, models


def copy_identity_verification_status(apps, schema_editor):
    CustomUser = apps.get_model('accounts', 'CustomUser')
    CustomUser.objects.filter(user_type='househelp', is_verified=True).update(
        is_identity_verified=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0020_delete_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='is_identity_verified',
            field=models.BooleanField(
                default=False,
                help_text='Identity verified through the Didit verification provider',
                verbose_name='Identity Verified',
            ),
        ),
        migrations.RunPython(copy_identity_verification_status, migrations.RunPython.noop),
    ]