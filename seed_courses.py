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
            'duration': "1 week (Self-paced)",
            'features': "Mandatory for all learners; certificate included.",
            'is_native': True,
            'iframe_url': "https://www.youtube.com/embed/dQw4w9WgXcQ"
        }
    )
    if not created:
        course_pro.price = 0
        course_pro.is_mandatory = True
        course_pro.duration = "1 week (Self-paced)"
        course_pro.features = "Mandatory for all learners; certificate included."
        course_pro.save()
    else:
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
            'price': 1500,
            'is_free': False,
            'is_mandatory': False,
            'duration': "2–3 weeks",
            'features': "Practical exercises, child safety tips, play & learning templates.",
            'is_native': True,
            'iframe_url': "https://www.youtube.com/embed/dQw4w9WgXcQ"
        }
    )
    if not created:
        course_child.price = 1500
        course_child.duration = "2–3 weeks"
        course_child.features = "Practical exercises, child safety tips, play & learning templates."
        course_child.save()
    else:
        print("- Created Course: Childcare")
        lesson = Lesson.objects.create(
            course=course_child,
            title="Basics of Infant Safety",
            content="When caring for young children, safety is your primary priority. Learn how to baby-proof a kitchen...",
            order=1
        )

    # 3. Chef & Kitchen Management
    course_chef, created = Course.objects.get_or_create(
        title="Chef & Kitchen Management",
        defaults={
            'description': "Learn advanced cooking techniques, food safety, and kitchen organization.",
            'price': 1800,
            'is_free': False,
            'is_mandatory': False,
            'duration': "3–4 weeks",
            'features': "Hands-on cooking, menu planning, hygiene guides.",
            'is_native': True,
            'iframe_url': "https://www.youtube.com/embed/dQw4w9WgXcQ"
        }
    )
    if not created:
        course_chef.price = 1800
        course_chef.duration = "3–4 weeks"
        course_chef.features = "Hands-on cooking, menu planning, hygiene guides."
        course_chef.save()
    else:
        print("- Created Course: Chef & Kitchen")

    # 4. Elderly Care
    course_elder, created = Course.objects.get_or_create(
        title="Elderly Care Specialist",
        defaults={
            'description': "Providing compassionate care for senior citizens, managing medication, and safety.",
            'price': 1500,
            'is_free': False,
            'is_mandatory': False,
            'duration': "3 weeks",
            'features': "Care exercises, emergency guidelines, emotional support strategies.",
            'is_native': True,
            'iframe_url': "https://www.youtube.com/embed/dQw4w9WgXcQ"
        }
    )
    if not created:
        course_elder.price = 1500
        course_elder.duration = "3 weeks"
        course_elder.features = "Care exercises, emergency guidelines, emotional support strategies."
        course_elder.save()
    else:
        print("- Created Course: Elderly Care")

    print("Course seeding complete!")

if __name__ == "__main__":
    seed_courses()
