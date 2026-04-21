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
from functools import wraps
import requests
import json
from django.conf import settings

def is_admin(user):
    return user.is_authenticated and user.is_staff

def first_time_verification_required(view_func):
    """Decorator to ensure housekeeper has completed first-time Didit verification"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.user_type == 'househelp':
            if not request.user.has_completed_first_verification:
                messages.warning(request, 'Please complete identity verification to access your dashboard.')
                return redirect('initiate_didit_verification')
        return view_func(request, *args, **kwargs)
    return wrapper

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
        
    # --- SYNCHRONOUS DIDIT CHECK FALLBACK ---
    if not request.user.has_completed_first_verification and request.user.didit_session_id:
        session_id = request.user.didit_session_id
        import logging
        logger = logging.getLogger(__name__)
        try:
            current_api_key = getattr(settings, 'DIDIT_API_KEY', '')
            headers = {"x-api-key": current_api_key}
            
            logger.info(f"Dashboard Load: Sync checking Didit Session {session_id} for user {request.user.id}")
            response = requests.get(f"https://verification.didit.me/v3/session/{session_id}/", headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                status_raw = data.get('status') or data.get('session', {}).get('status', '')
                status = str(status_raw).upper()
                logger.info(f"Didit API returned status for user {request.user.id}: {status}")
                
                if status in ['SUCCESS', 'APPROVED', 'COMPLETED']:
                    request.user.didit_verification_status = 'completed'
                    request.user.is_verified = True
                    request.user.badge_verified_id = True
                    request.user.has_completed_first_verification = True
                    request.user.save()
                    messages.success(request, "Identity verification successful! Your profile is verified.")
                elif status in ['FAILED', 'DECLINED', 'EXPIRED']:
                    request.user.didit_verification_status = status.lower()
                    request.user.save()
                    messages.error(request, f"Identity verification {status.lower()}. Please try again.")
            else:
                logger.error(f"Didit API Error {response.status_code} for user {request.user.id}: {response.text}")
        except Exception as e:
            logger.error(f"Error in Didit sync fallback for user {request.user.id}: {str(e)}")

    # ----------------------------------------

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
        total_courses = Course.objects.all().count()
        accessible_courses = Course.objects.exclude(id__in=completed_course_ids)
    else:
        total_courses = Course.objects.filter(id__in=completed_course_ids).count()
        paid_course_ids = Payment.objects.filter(user=request.user, course__isnull=False, status='completed').values_list('course_id', flat=True)
        accessible_courses = Course.objects.filter(
            models.Q(is_free=True) | models.Q(is_mandatory=True) | models.Q(id__in=paid_course_ids)
        ).exclude(id__in=completed_course_ids)

    completion_percentage = (len(completed_course_ids) / total_courses * 100) if total_courses > 0 else 0
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
        'completion_percentage': round(completion_percentage),
        'completed_courses_count': len(completed_course_ids),
        'total_courses_count': total_courses,
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
    applications = Application.objects.filter(
        job__employer=request.user
    ).exclude(
        models.Q(applicant__profile_picture='') | models.Q(applicant__profile_picture__isnull=True)
    ).select_related('applicant').order_by('-created_at')
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


@login_required
def force_didit_sync(request):
    """View to manually force a sync with Didit API"""
    if request.user.user_type != 'househelp':
        return redirect('home')
        
    session_id = request.user.didit_session_id
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        current_api_key = getattr(settings, 'DIDIT_API_KEY', '')
        headers = {"x-api-key": current_api_key}
        
        # ─── ATTEMPT 1: SYNC BY SESSION ID ─────────────────────────────────
        if session_id:
            logger.info(f"Manual Sync: Checking Didit Session {session_id} for user {request.user.id}")
            response = requests.get(f"https://verification.didit.me/v3/session/{session_id}/", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status_raw = data.get('status') or data.get('session', {}).get('status', '')
                status = str(status_raw).upper()
                
                if status in ['SUCCESS', 'APPROVED', 'COMPLETED']:
                    return _mark_user_verified(request, status)
        
        # ─── ATTEMPT 2: FALLBACK TO SEARCH BY VENDOR DATA ──────────────────
        logger.info(f"Manual Sync Fallback: Searching sessions for user {request.user.id}")
        search_url = f"https://verification.didit.me/v3/session/?vendor_data={request.user.id}"
        search_response = requests.get(search_url, headers=headers, timeout=10)
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            # Handle list response
            sessions = search_data if isinstance(search_data, list) else search_data.get('results', [])
            
            # Find the most recent successful session
            for s in sessions:
                status = str(s.get('status', '')).upper()
                if status in ['SUCCESS', 'APPROVED', 'COMPLETED']:
                    # Update the missing session ID too
                    request.user.didit_session_id = s.get('id')
                    return _mark_user_verified(request, status)
            
            if sessions:
                latest_status = sessions[0].get('status', 'unknown')
                messages.info(request, f"Found {len(sessions)} sessions, but none are approved yet (Latest: {latest_status}).")
            else:
                messages.warning(request, "No verification sessions found for your account on Didit.")
        else:
            logger.error(f"Manual Sync Search Error {search_response.status_code}: {search_response.text}")
            messages.error(request, "Could not reach verification service. Please try again later.")
            
    except Exception as e:
        logger.error(f"Manual Sync Error: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        
    return redirect('dashboard:housekeeper_dashboard')

def _mark_user_verified(request, status):
    """Helper to mark user as verified and return redirect"""
    request.user.didit_verification_status = 'completed'
    request.user.is_verified = True
    request.user.badge_verified_id = True
    request.user.has_completed_first_verification = True
    request.user.save()
    messages.success(request, f"Success! Your identity has been verified (Status: {status}).")
    return redirect('dashboard:housekeeper_dashboard')

        
    return redirect('dashboard:housekeeper_dashboard')