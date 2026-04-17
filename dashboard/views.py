from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Avg
from django.contrib import messages
from accounts.models import CustomUser
from jobs.models import Job, Application
from payments.models import Payment, PaymentPlan
from reviews.models import Review
from django.db import models
from courses.models import Course, CourseCompletion
from payments.models import MonthlyContribution
from accounts.models import PlatformDocument

def is_admin(user):
    return user.is_authenticated and user.is_staff

# ────────────────────────────────────────────────
# Admin Dashboard Views
# ────────────────────────────────────────────────

@user_passes_test(is_admin)
def dashboard_home(request):
    total_users = CustomUser.objects.count()
    total_housekeepers = CustomUser.objects.filter(user_type='househelp').count()
    total_employers = CustomUser.objects.filter(user_type='employer').count()
    total_jobs = Job.objects.count()
    total_applications = Application.objects.count()
    avg_rating = Review.objects.aggregate(Avg('rating'))['rating__avg'] or 0

    recent_users = CustomUser.objects.order_by('-date_joined')[:8]
    recent_jobs = Job.objects.order_by('-created_at')[:8]
    pending_payments_count = Payment.objects.filter(status='verification_submitted').count()

    context = {
        'total_users': total_users,
        'total_housekeepers': total_housekeepers,
        'total_employers': total_employers,
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'avg_rating': round(avg_rating, 1),
        'recent_users': recent_users,
        'recent_jobs': recent_jobs,
        'pending_payments_count': pending_payments_count,
    }
    return render(request, 'dashboard/home.html', context)


@user_passes_test(is_admin)
def dashboard_users(request):
    users = CustomUser.objects.select_related().order_by('-date_joined')
    pending_payments_count = Payment.objects.filter(status='verification_submitted').count()
    return render(request, 'dashboard/users.html', {
        'users': users,
        'pending_payments_count': pending_payments_count,
    })


@user_passes_test(is_admin)
def dashboard_jobs(request):
    jobs = Job.objects.select_related('employer').order_by('-created_at')
    pending_payments_count = Payment.objects.filter(status='verification_submitted').count()
    return render(request, 'dashboard/jobs.html', {
        'jobs': jobs,
        'pending_payments_count': pending_payments_count,
    })


@user_passes_test(is_admin)
def dashboard_applications(request):
    applications = Application.objects.select_related('job', 'job__employer', 'applicant').order_by('-created_at')
    pending_payments_count = Payment.objects.filter(status='verification_submitted').count()
    return render(request, 'dashboard/applications.html', {
        'applications': applications,
        'pending_payments_count': pending_payments_count,
    })


@user_passes_test(is_admin)
def dashboard_stats(request):
    jobs_by_city = Job.objects.values('city').annotate(count=Count('id')).order_by('-count')[:10]
    jobs_by_type = Job.objects.values('job_type').annotate(count=Count('id')).order_by('-count')
    applications_by_status = Application.objects.values('status').annotate(count=Count('id')).order_by('-count')
    
    users_by_type = [
        {'type': 'Housekeepers', 'count': CustomUser.objects.filter(user_type='househelp').count()},
        {'type': 'Employers', 'count': CustomUser.objects.filter(user_type='employer').count()},
    ]

    pending_payments_count = Payment.objects.filter(status='verification_submitted').count()

    context = {
        'jobs_by_city': jobs_by_city,
        'jobs_by_type': jobs_by_type,
        'applications_by_status': applications_by_status,
        'users_by_type': users_by_type,
        'pending_payments_count': pending_payments_count,
    }
    return render(request, 'dashboard/stats.html', context)

# ────────────────────────────────────────────────
# User Dashboards (redirect + specific views)
# ────────────────────────────────────────────────

@login_required
def user_dashboard(request):
    if request.user.user_type == 'househelp':
        return redirect('dashboard:housekeeper_dashboard')
    elif request.user.user_type == 'employer':
        return redirect('dashboard:employer_dashboard')
    messages.error(request, "Invalid user type.")
    return redirect('home')


@login_required
def housekeeper_dashboard(request):
    if request.user.user_type != 'househelp':
        messages.error(request, "Access denied. Housekeepers only.")
        return redirect('home')

    applications = Application.objects.filter(applicant=request.user).select_related('job').order_by('-created_at')
    active_jobs = Job.objects.filter(is_active=True).order_by('-created_at')[:10]

    reviews = Review.objects.filter(reviewed_user=request.user)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    review_count = reviews.count()
    skills_list = [s.strip() for s in (request.user.skills or '').split(',') if s.strip()]

    # Study Tracker Logic
    completed_course_ids = CourseCompletion.objects.filter(user=request.user).values_list('course_id', flat=True)
    has_bundle = Payment.objects.filter(user=request.user, plan__plan_type='academy_bundle', status='completed').exists()
    if has_bundle:
        accessible_courses = Course.objects.exclude(id__in=completed_course_ids)
    else:
        paid_course_ids = Payment.objects.filter(user=request.user, course__isnull=False, status='completed').values_list('course_id', flat=True)
        accessible_courses = Course.objects.filter(
            models.Q(is_free=True) | models.Q(is_mandatory=True) | models.Q(id__in=paid_course_ids)
        ).exclude(id__in=completed_course_ids)
    study_tracker_courses = accessible_courses.order_by('-is_mandatory')[:3]

    # Monthly Contribution logic
    pending_contribution = MonthlyContribution.objects.filter(worker=request.user, payment_status='pending').order_by('-year', '-month').first()

    # Agreements / Templates
    agreement_template = PlatformDocument.objects.filter(doc_type='worker_agreement', is_active=True).first()

    context = {
        'applications': applications,
        'active_jobs': active_jobs,
        'user': request.user,
        'avg_rating': round(avg_rating, 1),
        'review_count': review_count,
        'skills_list': skills_list,
        'study_tracker_courses': study_tracker_courses,
        'pending_contribution': pending_contribution,
        'agreement_template': agreement_template,
    }
    return render(request, 'dashboard/housekeeper_dashboard.html', context)


@login_required
def employer_dashboard(request):
    if request.user.user_type != 'employer':
        messages.error(request, "Access denied. Employers only.")
        return redirect('home')

    jobs = Job.objects.filter(employer=request.user).order_by('-created_at')
    applications = Application.objects.filter(job__employer=request.user).select_related('applicant').order_by('-created_at')
    payment_plans = PaymentPlan.objects.filter(is_active=True)

    reviews = Review.objects.filter(reviewed_user=request.user)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    review_count = reviews.count()

    context = {
        'jobs': jobs,
        'applications': applications,
        'user': request.user,
        'payment_plans': payment_plans,
        'avg_rating': round(avg_rating, 1),
        'review_count': review_count,
    }
    return render(request, 'dashboard/employer_dashboard.html', context)