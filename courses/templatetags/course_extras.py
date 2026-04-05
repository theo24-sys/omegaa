from django import template
from courses.models import Course, LessonCompletion

register = template.Library()

@register.filter
def get_course_progress(course_id, user):
    if not user.is_authenticated:
        return 0
    try:
        course = Course.objects.get(id=course_id)
        total_lessons = course.lessons.count()
        if total_lessons == 0:
            return 0
        completed_lessons = LessonCompletion.objects.filter(user=user, lesson__course=course).count()
        return int((completed_lessons / total_lessons) * 100)
    except Course.DoesNotExist:
        return 0
