"""
Script to add the 6 new certification courses to the database
Run with: python manage.py shell < add_courses.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housekeeper_connect.settings')
django.setup()

from courses.models import Course

def add_courses():
    """Add all 6 certification courses"""
    
    courses_data = [
        {
            'title': 'Professional Domestic Service Standards',
            'description': 'Master essential skills for professional domestic service including workplace boundaries, communication, and hygiene standards.',
            'price': 0,
            'discounted_price': 0,
            'iframe_url': 'https://my.coursebox.ai/courses/019d7153-c37e-740c-955f-f5a5f84f694e/about',
            'is_free': True,
            'is_mandatory': False,
            'duration': '1-2 weeks',
            'features': 'Professional standards, Workplace ethics, Communication skills, Hygiene protocols'
        },
        {
            'title': 'Childcare Assistant Certification',
            'description': 'Comprehensive training for childcare assistance including infant safety, early development, and childcare best practices.',
            'price': 1500,
            'discounted_price': 0,
            'iframe_url': 'https://my.coursebox.ai/courses/019d7153-c37f-7363-b5d2-e22a2cd57f4a/about',
            'is_free': False,
            'is_mandatory': False,
            'duration': '2-3 weeks',
            'features': 'Infant care, Child safety, Development milestones, Play & learning'
        },
        {
            'title': 'Elderly Care Support Certification',
            'description': 'Training for providing compassionate and professional elderly care, including health monitoring and personal care assistance.',
            'price': 1500,
            'discounted_price': 0,
            'iframe_url': 'https://my.coursebox.ai/courses/019d7153-c399-70cf-8afa-9ed53f258018/about',
            'is_free': False,
            'is_mandatory': False,
            'duration': '2-3 weeks',
            'features': 'Elderly care basics, Health monitoring, Personal care, Mobility assistance'
        },
        {
            'title': 'Home Care & Kitchen Essentials Certification',
            'description': 'Master home care management and kitchen essentials including food safety, nutrition, and kitchen organization.',
            'price': 1800,
            'discounted_price': 0,
            'iframe_url': 'https://my.coursebox.ai/courses/019d7153-c399-7a98-a651-3528c3666af5/about',
            'is_free': False,
            'is_mandatory': False,
            'duration': '2-3 weeks',
            'features': 'Home management, Food safety, Nutrition, Kitchen organization'
        },
        {
            'title': 'Household Appliance Safety and Maintenance',
            'description': 'Essential training on safely using and maintaining household appliances including troubleshooting common issues.',
            'price': 1200,
            'discounted_price': 0,
            'iframe_url': 'https://my.coursebox.ai/courses/019d9df0-38f9-7ccd-a446-ee2e274982ff/about',
            'is_free': False,
            'is_mandatory': False,
            'duration': '1-2 weeks',
            'features': 'Appliance safety, Maintenance tips, Troubleshooting, Energy efficiency'
        },
        {
            'title': 'Garments and Laundry Care Certification',
            'description': 'Complete training on garment care, laundry management, stain removal, and fabric handling for professional results.',
            'price': 700,
            'discounted_price': 0,
            'iframe_url': 'https://my.coursebox.ai/courses/019d7153-c40d-7258-a87d-31b5bd9360a1/about',
            'is_free': False,
            'is_mandatory': False,
            'duration': '1-2 weeks',
            'features': 'Laundry basics, Stain removal, Fabric care, Garment storage'
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    for course_data in courses_data:
        course, created = Course.objects.get_or_create(
            title=course_data['title'],
            defaults=course_data
        )
        
        if created:
            print(f"✓ Created: {course_data['title']} (KES {course_data['price']})")
            created_count += 1
        else:
            # Update existing course with latest data
            for key, value in course_data.items():
                if key != 'title':
                    setattr(course, key, value)
            course.save()
            print(f"✓ Updated: {course_data['title']} (KES {course_data['price']})")
            updated_count += 1
    
    print(f"\n✓ Course seeding complete!")
    print(f"  Created: {created_count}")
    print(f"  Updated: {updated_count}")
    print(f"  Total: {created_count + updated_count}")

if __name__ == '__main__':
    add_courses()
