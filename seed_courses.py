import os
import django

# Set up the Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housekeeper_connect.settings')
django.setup()

from courses.models import Course, Lesson, Question, Choice

def seed_courses():
    print("Starting course seeding...")

    # helper to ensure lessons exist
    def ensure_lesson(course, title, content, video_url="", order=1):
        lesson, created = Lesson.objects.get_or_create(
            course=course,
            title=title,
            defaults={'content': content, 'video_url': video_url, 'order': order}
        )
        if not created:
            lesson.content = content
            lesson.video_url = video_url
            lesson.order = order
            lesson.save()
        return lesson

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
    # Always update metadata
    course_pro.price = 0
    course_pro.is_mandatory = True
    course_pro.duration = "1 week (Self-paced)"
    course_pro.features = "Mandatory for all learners; certificate included."
    course_pro.is_native = True
    course_pro.save()

    # Ensure Lesson 1
    lesson = ensure_lesson(
        course_pro, 
        "Introduction to Professionalism", 
        "Professionalism is about your attitude, your appearance, and how you treat the homes you work in. Key areas include punctuality, honest communication with employers, and maintaining high hygiene standards.",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        1
    )
    
    # Ensure Questions
    q1, _ = Question.objects.get_or_create(course=course_pro, lesson=lesson, text="What is the most important part of workplace boundaries?", defaults={'order': 1})
    if not q1.choices.exists():
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
    course_child.price = 1500
    course_child.duration = "2–3 weeks"
    course_child.features = "Practical exercises, child safety tips, play & learning templates."
    course_child.is_native = True
    course_child.save()

    ensure_lesson(
        course_child,
        "Basics of Infant Safety",
        "When caring for young children, safety is your primary priority. Learn how to baby-proof a kitchen, safe sleep positions for infants, and basic first aid for choking.",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        1
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
    course_chef.price = 1800
    course_chef.duration = "3–4 weeks"
    course_chef.features = "Hands-on cooking, menu planning, hygiene guides."
    course_chef.is_native = True
    course_chef.save()

    ensure_lesson(
        course_chef,
        "Kitchen Hygiene & Safety",
        "A managed kitchen is a safe kitchen. Learn about cross-contamination prevention, knife skills for professionals, and efficient grocery planning.",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        1
    )

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
    course_elder.price = 1500
    course_elder.duration = "3 weeks"
    course_elder.features = "Care exercises, emergency guidelines, emotional support strategies."
    course_elder.is_native = True
    course_elder.save()

    ensure_lesson(
        course_elder,
        "Introduction to Geriatric Care",
        "Understanding the unique needs of the elderly — from physical mobility assistance to providing emotional companionship and managing daily medication schedules safely.",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        1
    )

    print("Course seeding complete!")

if __name__ == "__main__":
    seed_courses()
