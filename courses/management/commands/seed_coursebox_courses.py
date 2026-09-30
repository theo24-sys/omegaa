"""
Seed the 6 real Coursebox certification courses and hide the placeholder demos.

Usage: python manage.py seed_coursebox_courses
Idempotent: safe to run on every deploy (get_or_create + metadata refresh).
"""
from django.core.management.base import BaseCommand
from courses.models import Course

COURSEBOX_BASE = 'https://my.coursebox.ai/courses'

COURSES_DATA = [
    {
        'title': 'Professional Domestic Service Standards',
        'description': 'Master essential skills for professional domestic service including workplace boundaries, communication, and hygiene standards.',
        'price': 0,
        'discounted_price': 0,
        'iframe_url': f'{COURSEBOX_BASE}/019d7153-c37e-740c-955f-f5a5f84f694e/about',
        'is_free': True,
        'is_mandatory': False,
        'duration': '1-2 weeks',
        'features': 'Professional standards, Workplace ethics, Communication skills, Hygiene protocols',
    },
    {
        'title': 'Childcare Assistant Certification',
        'description': 'Comprehensive training for childcare assistance including infant safety, early development, and childcare best practices. 5 sections - 21 lessons.',
        'price': 1500,
        'discounted_price': 0,
        'iframe_url': f'{COURSEBOX_BASE}/019d7153-c37f-7363-b5d2-e22a2cd57f4a/about',
        'is_free': False,
        'is_mandatory': False,
        'duration': '2-3 weeks',
        'features': 'Infant care, Child safety, Development milestones, Play & learning',
    },
    {
        'title': 'Elderly Care Support Certification',
        'description': 'Training for providing compassionate and professional elderly care, including health monitoring and personal care assistance.',
        'price': 1500,
        'discounted_price': 0,
        'iframe_url': f'{COURSEBOX_BASE}/019d7153-c399-70cf-8afa-9ed53f258018/about',
        'is_free': False,
        'is_mandatory': False,
        'duration': '2-3 weeks',
        'features': 'Elderly care basics, Health monitoring, Personal care, Mobility assistance',
    },
    {
        'title': 'Home Care & Kitchen Essentials Certification',
        'description': 'Master home care management and kitchen essentials including food safety, nutrition, and kitchen organization.',
        'price': 1800,
        'discounted_price': 0,
        'iframe_url': f'{COURSEBOX_BASE}/019d7153-c399-7a98-a651-3528c3666af5/about',
        'is_free': False,
        'is_mandatory': False,
        'duration': '2-3 weeks',
        'features': 'Home management, Food safety, Nutrition, Kitchen organization',
    },
    {
        'title': 'Household Appliance Safety and Maintenance',
        'description': 'Essential training on safely using and maintaining household appliances including troubleshooting common issues.',
        'price': 1200,
        'discounted_price': 0,
        'iframe_url': f'{COURSEBOX_BASE}/019d9df0-38f9-7ccd-a446-ee2e274982ff/about',
        'is_free': False,
        'is_mandatory': False,
        'duration': '1-2 weeks',
        'features': 'Appliance safety, Maintenance tips, Troubleshooting, Energy efficiency',
    },
    {
        'title': 'Garments and Laundry Care Certification',
        'description': 'Complete training on garment care, laundry management, stain removal, and fabric handling for professional results.',
        'price': 700,
        'discounted_price': 0,
        'iframe_url': f'{COURSEBOX_BASE}/019d7153-c40d-7258-a87d-31b5bd9360a1/about',
        'is_free': False,
        'is_mandatory': False,
        'duration': '1-2 weeks',
        'features': 'Laundry basics, Stain removal, Fabric care, Garment storage',
    },
]

# Placeholder demo courses created by the old seeder — hidden once the
# real Coursebox versions exist.
PLACEHOLDER_TITLES = [
    'Professional Standards & Ethics',
    'Childcare & Early Development',
    'Elderly Care Specialist',
    'Chef & Kitchen Management',
]


class Command(BaseCommand):
    help = 'Seed the 6 Coursebox certification courses and hide placeholder demos'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for data in COURSES_DATA:
            course, created = Course.objects.get_or_create(
                title=data['title'],
                defaults=data,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {data['title']} (KES {data['price']})"))
            else:
                for key, value in data.items():
                    if key != 'title':
                        setattr(course, key, value)
                course.is_active = True  # re-show if previously hidden
                course.save()
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"Updated: {data['title']} (KES {data['price']})"))

        hidden = Course.objects.filter(title__in=PLACEHOLDER_TITLES, is_active=True)
        for course in hidden:
            course.is_active = False
            course.save(update_fields=['is_active'])
            self.stdout.write(self.style.NOTICE(f"Hidden placeholder: {course.title}"))

        total_active = Course.objects.filter(is_active=True).count()
        self.stdout.write(self.style.SUCCESS(
            f"\nCoursebox seeding complete! Created: {created_count}, Updated: {updated_count}, "
            f"Hidden placeholders: {hidden.count()}, Active courses: {total_active}"
        ))
