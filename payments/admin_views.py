from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Payment
from notifications.utils import create_notification

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def pending_payments(request):
    pending_payments = Payment.objects.filter(status='verification_submitted').order_by('-created_at')
    
    context = {
        'pending_payments': pending_payments,
    }
    return render(request, 'payments/admin/pending_payments.html', context)

@user_passes_test(is_admin)
def verify_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        
        payment.admin_notes = admin_notes
        
        if action == 'approve':
            # Update payment status
            payment.status = 'completed'
            payment.save()
            
            # Apply the benefits based on the plan type
            if payment.plan.plan_type == 'job_boost':
                # Find the user's most recent job and make it featured
                job = payment.user.jobs.filter(is_active=True).order_by('-created_at').first()
                if job:
                    job.is_featured = True
                    job.featured_until = timezone.now() + timedelta(days=payment.plan.duration_days)
                    job.save()
            
            elif payment.plan.plan_type == 'profile_highlight':
                # Make the user's profile premium
                user = payment.user
                user.is_premium = True
                user.premium_until = timezone.now() + timedelta(days=payment.plan.duration_days)
                user.save()

            elif payment.plan.plan_type == 'verification':
                # Verify the user for membership
                user = payment.user
                user.is_verified = True
                user.save()
            
            # Create notification for the user
            create_notification(
                recipient=payment.user,
                notification_type='system',
                title='Payment Approved',
                message=f'Your payment for {payment.plan.name} has been verified and approved. The benefits are now active.',
                related_object=payment
            )
            
            messages.success(request, f'Payment for {payment.user.username} has been approved.')
        
        elif action == 'reject':
            # Update payment status
            payment.status = 'failed'
            payment.save()
            
            # Create notification for the user
            create_notification(
                recipient=payment.user,
                notification_type='system',
                title='Payment Rejected',
                message=f'Your payment for {payment.plan.name} could not be verified. Please contact admin for assistance.',
                related_object=payment
            )
            
            messages.warning(request, f'Payment for {payment.user.username} has been rejected.')
        
        return redirect('payments:admin_pending_payments')
    
    context = {
        'payment': payment,
    }
    return render(request, 'payments/admin/verify_payment.html', context)

@user_passes_test(is_admin)
def all_payments(request):
    payments = Payment.objects.all().order_by('-created_at')
    
    context = {
        'payments': payments,
    }
    return render(request, 'payments/admin/all_payments.html', context)

