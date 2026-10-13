from django.db import migrations, models


def populate_badge_keys(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    mappings = (
        ('professional', 'professional_standards'),
        ('standard', 'professional_standards'),
        ('childcare', 'childcare'),
        ('elderly', 'eldercare'),
        ('elder care', 'eldercare'),
        ('kitchen', 'kitchen'),
        ('chef', 'kitchen'),
        ('appliance', 'appliance'),
        ('cleaning', 'cleaning'),
        ('home care', 'cleaning'),
    )
    for course in Course.objects.filter(badge_key=''):
        title = course.title.lower()
        for fragment, badge_key in mappings:
            if fragment in title:
                course.badge_key = badge_key
                course.save(update_fields=['badge_key'])
                break


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0007_course_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='badge_key',
            field=models.CharField(blank=True, choices=[('professional_standards', 'Professional Standards'), ('cleaning', 'Cleaning'), ('childcare', 'Childcare'), ('eldercare', 'Elder Care'), ('kitchen', 'Kitchen'), ('appliance', 'Appliance')], default='', max_length=40),
        ),
        migrations.RunPython(populate_badge_keys, migrations.RunPython.noop),
    ]