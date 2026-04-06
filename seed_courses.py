import os
import django

# Set up the Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housekeeper_connect.settings')
django.setup()

from courses.models import Course, Lesson, Question, Choice

def seed_courses():
    print("Starting course seeding...")

    # 1. Professional Standards & Ethics (Mandatory)
    course_pro, created = Course.objects.get_or_create(
        title="Professional Standards & Ethics",
        defaults={
            'description': "Essential training for every modern housekeeper. Master workplace boundaries, communication, and hygiene.",
            'price': 0,
            'is_free': True,
            'is_mandatory': True,
            'is_native': True,
            'iframe_url': "https://www.youtube.com/embed/dQw4w9WgXcQ" # Placeholder
        }
    )
    if created:
        print("- Created Course: Professional Standards")
        lesson = Lesson.objects.create(
            course=course_pro,
            title="Introduction to Professionalism",
            content="Professionalism is about your attitude, your appearance, and how you treat the homes you work in...",
            video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
            order=1
        )
        q1 = Question.objects.create(course=course_pro, lesson=lesson, text="What is the most important part of workplace boundaries?", order=1)
        Choice.objects.create(question=q1, text="Respecting privacy and confidentiality", is_correct=True)
        Choice.objects.create(question=q1, text="Arriving late every day", is_correct=False)
        Choice.objects.create(question=q1, text="Using the employer's phone without asking", is_correct=False)

    # 2. Childcare & Safety
    course_child, created = Course.objects.get_or_create(
        title="Childcare & Early Development",
        defaults={
            'description': "Specialized training for caring for infants and toddlers, including first aid and nutrition.",
            'price': 500,
            'is_free': False,
            'is_mandatory': False,
            'is_native': True,
            'iframe_url': "https://www.youtube.com/embed/dQw4w9WgXcQ"
        }
    )
    if created:
        print("- Created Course: Childcare")
        lesson = Lesson.objects.create(
            course=course_child,
            title="Basics of Infant Safety",
            content="When caring for young children, safety is your primary priority. Learn how to baby-proof a kitchen...",
            order=1
        )
        q1 = Question.objects.create(course=course_child, lesson=lesson, text="How should a baby sleep to prevent SIDS?", order=1)
        Choice.objects.create(question=q1, text="On their back", is_correct=True)
        Choice.objects.create(question=q1, text="On their stomach", is_correct=False)
        Choice.objects.create(question=q1, text="With a thick pillow", is_correct=False)

    # 3. Chef & Kitchen Management
    course_chef, created = Course.objects.get_or_create(
        title="Chef & Kitchen Management",
        defaults={
            'description': "Learn advanced cooking techniques, food safety, and kitchen organization.",
            'price': 500,
            'is_free': False,
            'is_mandatory': False,
            'is_native': True,
            'iframe_url': "https://www.youtube.com/embed/dQw4w9WgXcQ"
        }
    )
    if created:
        print("- Created Course: Chef & Kitchen")
        Lesson.objects.create(course=course_chef, title="Food Hygiene & Safe Handling", order=1)

    # 4. Elderly Care
    course_elder, created = Course.objects.get_or_create(
        title="Elderly Care Specialist",
        defaults={
            'description': "Providing compassionate care for senior citizens, managing medication, and safety.",
            'price': 500,
            'is_free': False,
            'is_mandatory': False,
            'is_native': True,
            'iframe_url': "https://www.youtube.com/embed/dQw4w9WgXcQ"
        }
    )
    if created:
        print("- Created Course: Elderly Care")
        Lesson.objects.create(course=course_elder, title="Understanding Senior Needs", order=1)

    print("Course seeding complete!")

if __name__ == "__main__":
    seed_courses()
