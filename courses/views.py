from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Course, CourseCompletion
from payments.models import Payment

@login_required
def course_list(request):
    courses = Course.objects.all().order_by('-is_mandatory', 'price')
    completed_courses = CourseCompletion.objects.filter(user=request.user).values_list('course_id', flat=True)
    paid_courses = Payment.objects.filter(user=request.user, status='completed').values_list('course_id', flat=True)
    
    context = {
        'courses': courses,
        'completed_courses': completed_courses,
        'paid_courses': paid_courses,
    }
    return render(request, 'courses/course_list.html', context)

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user has access (free, mandatory, or paid)
    has_access = False
    if course.is_free or course.is_mandatory:
        has_access = True
    else:
        # Check for completed payment
        has_access = Payment.objects.filter(
            user=request.user, 
            course=course, 
            status='completed'
        ).exists()
        
        # Also check if already completed (might have been paid before)
        if not has_access:
            has_access = CourseCompletion.objects.filter(user=request.user, course=course).exists()

    if not has_access:
        messages.info(request, f"Review the details for {course.title}. Payment is required to access lessons and earn certifications.")
        return redirect('course_checkout', course_id=course.id)

    completed_courses = CourseCompletion.objects.filter(user=request.user).values_list('course_id', flat=True)
    lessons = course.lessons.all() if course.is_native else []

    context = {
        'course': course,
        'completed_courses': completed_courses,
        'lessons': lessons,
    }
    return render(request, 'courses/course_detail.html', context)

@login_required
def lesson_detail(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    lessons = course.lessons.all()
    
    # Access check
    has_access = False
    if course.is_free or course.is_mandatory:
        has_access = True
    else:
        has_access = Payment.objects.filter(user=request.user, course=course, status='completed').exists()
        if not has_access:
            has_access = CourseCompletion.objects.filter(user=request.user, course=course).exists()

    if not has_access:
        messages.warning(request, f"You need to pay for the {course.title} course to access this lesson.")
        return redirect('course_checkout', course_id=course.id)

    # Sequential Unlocking Check
    previous_lessons = lessons.filter(order__lt=lesson.order).order_by('order')
    for prev in previous_lessons:
        if not LessonCompletion.objects.filter(user=request.user, lesson=prev).exists():
            messages.info(request, f"Please complete '{prev.title}' before moving to this lesson.")
            return redirect('lesson_detail', course_id=course.id, lesson_id=prev.id)

    # Check if quiz exists for THIS lesson
    lesson_quiz_done = False
    if lesson.quiz_questions.exists():
        lesson_quiz_done = QuizAttempt.objects.filter(user=request.user, lesson=lesson, passed=True).exists()

    context = {
        'course': course,
        'lesson': lesson,
        'lessons': lessons,
        'lesson_quiz_done': lesson_quiz_done,
    }
    return render(request, 'courses/lesson_detail.html', context)

@login_required
def course_quiz(request, course_id, lesson_id=None):
    course = get_object_or_404(Course, id=course_id)
    lesson = None
    if lesson_id:
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
        questions = lesson.quiz_questions.all()
    else:
        # Final Exam - Randomize 40 questions (or all if < 40)
        questions = list(course.questions.filter(is_final_exam=True))
        import random
        random.shuffle(questions)
        questions = questions[:40]
    
    if request.method == 'POST':
        score = 0
        total = len(questions) if not lesson_id else questions.count()
        
        for q_id in request.POST:
            if q_id.startswith('question_'):
                id_val = q_id.split('_')[1]
                selected_choice_id = request.POST.get(q_id)
                if selected_choice_id:
                    try:
                        choice = Choice.objects.get(id=selected_choice_id, question_id=id_val)
                        if choice.is_correct:
                            score += 1
                    except Choice.DoesNotExist:
                        pass
        
        pass_threshold = 0.8  # 80%
        passed = (score / total) >= pass_threshold if total > 0 else False
        
        # Record attempt
        QuizAttempt.objects.create(
            user=request.user, course=course, lesson=lesson,
            score=score, total_questions=total, passed=passed,
            is_final=(lesson_id is None)
        )
        
        if passed:
            if lesson:
                LessonCompletion.objects.get_or_create(user=request.user, lesson=lesson)
                messages.success(request, f"Passed! You scored {score}/{total} ({(score/total)*100:.0f}%). Lesson completed.")
                return redirect('course_detail', course_id=course.id)
            else:
                return redirect('complete_course', course_id=course.id)
        else:
            messages.error(request, f"You scored {score}/{total} ({(score/total)*100:.0f}%). You need 80% to pass. Try again!")
            return redirect(request.path)
            
    context = {
        'course': course,
        'lesson': lesson,
        'questions': questions,
    }
    return render(request, 'courses/course_quiz.html', context)

@login_required
def complete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Create completion record
    completion, created = CourseCompletion.objects.get_or_create(user=request.user, course=course)
    
    if created:
        # Update user badges according to course title or some mapping
        user = request.user
        if "Professional Standards" in course.title:
            user.badge_professional_standards = True
        elif "Childcare" in course.title:
            user.badge_childcare = True
        elif "Elderly Care" in course.title:
            user.badge_elder_care = True
        elif "Home Care & Kitchen" in course.title:
            user.badge_cleaning = True  # Using cleaning as proxy for Home Care/Laundry
            user.badge_kitchen = True
        elif "Cleaning" in course.title:
            user.badge_cleaning = True
        elif "Kitchen" in course.title or "Cooking" in course.title:
            user.badge_kitchen = True
        
        user.save()
        messages.success(request, f"Congratulations! You have completed {course.title} and earned a badge.")
    
    return redirect('course_list')
