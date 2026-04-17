from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Job, Application
from .forms import JobForm, ApplicationForm, JobSearchForm
from notifications.utils import create_notification
from payments.models import Payment
from payments.mpesa_service import get_mpesa_client
from django.conf import settings

def job_list(request):
    form = JobSearchForm(request.GET or None)
    jobs = Job.objects.filter(is_active=True).order_by('-created_at')

    if form.is_valid():
        keyword = form.cleaned_data.get('keyword')
        city = form.cleaned_data.get('city')
        salary_min = form.cleaned_data.get('salary_min')
        job_type = form.cleaned_data.get('job_type')
        experience_level = form.cleaned_data.get('experience_level')

        if keyword:
            jobs = jobs.filter(
                Q(title__icontains=keyword) |
                Q(description__icontains=keyword) |
                Q(requirements__icontains=keyword)
            )
        if city:
            jobs = jobs.filter(city=city)
        if salary_min:
            jobs = jobs.filter(salary__gte=salary_min)
        if job_type:
            jobs = jobs.filter(job_type=job_type)
        if experience_level:
            jobs = jobs.filter(experience_level=experience_level)

    context = {
        'jobs': jobs,
        'form': form,
    }
    return render(request, 'jobs/job_list.html', context)


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)
    has_applied = False

    if request.user.is_authenticated and request.user.user_type == 'househelp':
        has_applied = Application.objects.filter(job=job, applicant=request.user).exists()

    context = {
        'job': job,
        'has_applied': has_applied,
    }
    return render(request, 'jobs/job_detail.html', context)


@login_required
def job_create(request):
    if request.user.user_type != 'employer':
        messages.error(request, 'Only employers can post jobs.')
        return redirect('jobs:job_list')

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = request.user
            job.save()  # Save first so we have ID

            # Payment logic (250 KES via STK Push)
            mpesa_code = request.POST.get('mpesa_code')
            phone_number = request.POST.get('phone_number') # Get phone for STK push
            
            job_fee = getattr(settings, 'JOB_POSTING_FEE', 250)
            
            # Create a generic payment record first
            payment = Payment.objects.create(
                user=request.user,
                amount=job_fee,
                payment_method='mpesa',
                status='pending',
                verification_notes=f"Job Posting fee for '{job.title}'"
            )
            
            if mpesa_code:
                # Fallback to manual code if provided
                job.mpesa_code = mpesa_code
                job.posting_fee_paid = False 
                job.save()
                payment.transaction_id = mpesa_code
                payment.status = 'verification_submitted'
                payment.save()
                messages.success(request, f'Job posted! Payment verification for KSh {job_fee} submitted.')
            elif phone_number:
                # Professional API Flow: STK Push
                client = get_mpesa_client()
                response = client.initiate_stk_push(
                    phone_number=phone_number,
                    amount=job_fee,
                    reference_id=f"JOB{job.id}",
                    description=f"Job Post Fee"
                )
                
                if response.get('success'):
                    payment.stk_reference_id = response.get('checkout_request_id')
                    payment.is_mpesa_stk = True
                    payment.phone_number = phone_number
                    payment.save()
                    messages.success(request, f'M-Pesa prompt sent! Complete payment of KSh {job_fee} on your phone to activate.')
                    return redirect('payments:mpesa_payment', payment_id=payment.id)
                else:
                    messages.error(request, f"M-Pesa error: {response.get('message')}. Please pay manually.")
            else:
                messages.warning(request, f'Please pay KSh {job_fee} to Till 4567052 to activate your job.')

            return redirect('jobs:my_jobs')
    else:
        form = JobForm()

    return render(request, 'jobs/job_form.html', {'form': form, 'action': 'Post New Job'})


@login_required
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.user != job.employer:
        messages.error(request, 'You can only edit your own jobs.')
        return redirect('jobs:job_detail', pk=pk)

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job updated successfully.')
            return redirect('jobs:job_detail', pk=pk)
    else:
        form = JobForm(instance=job)

    return render(request, 'jobs/job_form.html', {'form': form, 'action': 'Edit Job'})


@login_required
def job_delete(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.user != job.employer:
        messages.error(request, 'You can only delete your own jobs.')
        return redirect('jobs:job_detail', pk=pk)

    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job deleted.')
        return redirect('jobs:my_jobs')

    return render(request, 'jobs/job_confirm_delete.html', {'job': job})


@login_required
def job_apply(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)

    if request.user.user_type != 'househelp':
        messages.error(request, 'Only housekeepers can apply.')
        return redirect('jobs:job_detail', pk=pk)

    if not request.user.can_apply_for_jobs():
        messages.warning(
            request,
            'Please pay for Membership Verification before applying for jobs. Go to Payment Plans to activate your account.'
        )
        return redirect('payments:payment_plans')

    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.info(request, 'You already applied for this job.')
        return redirect('jobs:job_detail', pk=pk)

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()

            # Notify employer
            create_notification(
                recipient=job.employer,
                notification_type='job_application',
                title=f"New Application: {job.title}",
                message=f"{request.user.get_full_name() or request.user.username} has applied! View details on Charlady.",
                related_object=application,
                send_sms=True
            )

            messages.success(request, 'Application submitted!')
            return redirect('jobs:my_applications')
    else:
        form = ApplicationForm()

    return render(request, 'jobs/job_apply.html', {'form': form, 'job': job})


@login_required
def my_jobs(request):
    if request.user.user_type != 'employer':
        messages.error(request, 'Only employers can view this page.')
        return redirect('jobs:job_list')

    jobs = Job.objects.filter(employer=request.user).order_by('-created_at')
    return render(request, 'jobs/my_jobs.html', {'jobs': jobs})


@login_required
def my_applications(request):
    if request.user.user_type == 'employer':
        applications = Application.objects.filter(job__employer=request.user).select_related('applicant', 'job')
    else:
        applications = Application.objects.filter(applicant=request.user).select_related('job', 'job__employer')

    return render(request, 'jobs/my_applications.html', {'applications': applications})


@login_required
def update_application_status(request, pk):
    application = get_object_or_404(Application, pk=pk)

    if request.user != application.job.employer:
        messages.error(request, 'You can only update applications for your jobs.')
        return redirect('jobs:my_applications')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Application.STATUS_CHOICES):
            old_status = application.status
            application.status = new_status
            application.save()

            # Notify applicant
            create_notification(
                recipient=application.applicant,
                notification_type='application_status',
                title=f"Update: {application.job.title}",
                message=f"Your application status is now: {application.get_status_display()}. Log in to Charlady for next steps.",
                related_object=application,
                send_sms=True
            )

            messages.success(request, 'Status updated.')
        else:
            messages.error(request, 'Invalid status.')

    return redirect('jobs:my_applications')