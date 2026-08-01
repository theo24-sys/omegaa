from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.cache import cache
from .models import PaymentPlan, Payment, UserSubscription, MonthlyContribution
from jobs.models import Job
from courses.models import Course
from notifications.utils import create_notification
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import logging
from .mpesa_service import MpesaClient
from accounts.utils import normalize_kenyan_phone, validate_kenyan_phone

logger = logging.getLogger(__name__)

@login_required
def payment_plans(request):
    user_type = getattr(request.user, 'user_type', 'employer')
    
    if user_type == 'househelp':
        worker_plans = PaymentPlan.objects.filter(target_group='worker', is_active=True).order_by('price')
        return render(request, 'payments/worker_plans.html', {
            'plans': worker_plans
        })
    else:
        # User is employer - map to 0, 150, 350 plans
        standard_plan = PaymentPlan.objects.filter(target_group='employer', price=150, is_active=True).first()
        gold_plan = PaymentPlan.objects.filter(target_group='employer', price=350, is_active=True).first()
        free_plan = PaymentPlan.objects.filter(target_group='employer', price=0, is_active=True).first()
        
        return render(request, 'payments/plans.html', {
            'standard_plan': standard_plan,
            'pro_plan': gold_plan, # Maintain context variable name 'pro_plan'
            'free_plan': free_plan
        })


@login_required
def checkout(request, plan_id):
    plan = get_object_or_404(PaymentPlan, id=plan_id, is_active=True)

    if request.method == 'POST':
        payment = Payment.objects.create(
            user=request.user,
            plan=plan,
            amount=plan.price,
            payment_method='mpesa',
            status='pending'
        )
        return redirect('payments:mpesa_payment', payment_id=payment.id)

    return render(request, 'payments/checkout.html', {'plan': plan})


@login_required
def course_checkout(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        payment = Payment.objects.create(
            user=request.user,
            course=course,
            amount=course.discounted_price if course.discounted_price > 0 else course.price,
            payment_method='mpesa',
            status='pending'
        )
        return redirect('payments:mpesa_payment', payment_id=payment.id)

    return render(request, 'payments/course_checkout.html', {'course': course})


@login_required
def pay_contribution(request, contribution_id):
    contribution = get_object_or_404(MonthlyContribution, id=contribution_id, worker=request.user)
    
    # If already paid, or zero amount (ignored), just go back to history/dashboard
    if contribution.payment_status in ['paid', 'ignored']:
        messages.info(request, "This contribution has already been settled.")
        return redirect('dashboard')

    # Create a payment record
    payment = Payment.objects.create(
        user=request.user,
        contribution=contribution,
        amount=contribution.amount_due,
        payment_method='mpesa',
        status='pending'
    )
    
    # Redirect to the M-Pesa STK push page
    return redirect('payments:mpesa_payment', payment_id=payment.id)


@login_required
def mpesa_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    # If already completed or submitted, redirect away from payment input
    if payment.status == 'completed':
        return redirect('payments:payment_detail', payment_id=payment.id)
    if payment.status == 'verification_submitted':
        return redirect('payments:payment_verification_submitted', payment_id=payment.id)

    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')
        phone_number = request.POST.get('phone_number')
        notes = request.POST.get('verification_notes', '')

        if not transaction_id or not phone_number:
            messages.error(request, 'Transaction ID and phone number are required.')
            return redirect('payments:mpesa_payment', payment_id=payment.id)

        payment.transaction_id = transaction_id
        payment.phone_number = phone_number
        payment.verification_notes = notes
        payment.status = 'verification_submitted'
        payment.payment_date = timezone.now()
        payment.save()

        # Handle Course vs Plan for notifications
        name = payment.plan.name if payment.plan else (payment.course.title if payment.course else "Item")

        # Notify user
        create_notification(
            recipient=request.user,
            notification_type='system',
            title='Payment Submitted',
            message=f'Your payment for {name} is pending verification.',
            related_object=payment
        )

        # Notify admins
        from django.contrib.auth import get_user_model
        for admin in get_user_model().objects.filter(is_staff=True):
            create_notification(
                recipient=admin,
                notification_type='system',
                title='New Payment to Verify',
                message=f'User {payment.user.username} submitted payment for {name}.',
                related_object=payment
            )

        messages.success(request, 'Payment details submitted. We will verify shortly.')
        return redirect('payments:payment_verification_submitted', payment_id=payment.id)

    # Automatically trigger STK push if phone number provided via query or last payment
    stk_error = None
    
    # If the payment failed, display the failure reason as the error
    if payment.status == 'failed' and payment.verification_notes:
        stk_error = payment.verification_notes

    if request.method == 'GET' and 'trigger_stk' in request.GET:
        phone = request.GET.get('phone') or request.user.phone_number or ""
        if phone:
            # Check for zero amount
            if payment.amount <= 0:
                stk_error = "Payment amount must be greater than 0."
            else:
                # Normalize for M-Pesa using central utility
                normalized_phone = normalize_kenyan_phone(phone)
                if not normalized_phone:
                    stk_error = "Invalid Kenyan phone number format. Use 07... or 254..."
                else:
                    client = MpesaClient()
                    name = payment.plan.name if payment.plan else (payment.course.title if payment.course else "Service")
                    
                    # Start STK Push
                    res = client.initiate_stk_push(
                        phone_number=normalized_phone,
                        amount=payment.amount,
                        reference_id=str(payment.id),
                        description=f"Payment for {name}"
                    )
                    
                    if res.get('success'):
                        payment.is_mpesa_stk = True
                        payment.phone_number = normalized_phone
                        payment.stk_reference_id = res.get('checkout_request_id')
                        payment.stk_initiated_at = timezone.now()
                        payment.save()
                        messages.info(request, "An M-Pesa prompt has been sent to your phone.")
                    else:
                        stk_error = res.get('message')

    return render(request, 'payments/mpesa_payment.html', {
        'payment': payment,
        'till_number': settings.MPESA_TILL_NUMBER,
        'stk_error': stk_error,
        'phone_number': payment.phone_number
    })


@csrf_exempt
def mpesa_callback(request):
    """
    Endpoint for Safaricom to POST payment results
    CRITICAL: Idempotent - must not process same callback twice
    SECURITY: Rate limited to prevent DDoS attacks
    """
    if request.method != 'POST':
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid request method"}, status=405)

    # ─── RATE LIMITING: Prevent DDoS ──────────────────────────────────────────
    # Limit: 100 callbacks per hour per IP
    client_ip = request.META.get('REMOTE_ADDR', 'unknown')
    rate_limit_key = f'mpesa_callback_rate_{client_ip}'
    
    current_count = cache.get(rate_limit_key, 0)
    if current_count >= 100:
        logger.warning(f"M-Pesa callback rate limit exceeded for IP {client_ip}")
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Rate limit exceeded"}, status=429)
    
    cache.set(rate_limit_key, current_count + 1, 3600)  # 1 hour window
    # ──────────────────────────────────────────────────────────────────────────

    try:
        data = json.loads(request.body)
        stk_callback = data.get('Body', {}).get('stkCallback', {})
        result_code = stk_callback.get('ResultCode')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        
        # Find matching payment
        payment = Payment.objects.filter(stk_reference_id=checkout_request_id).first()
        if not payment:
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Payment record not found"}, status=404)

        # ─── IDEMPOTENCY CHECK ─────────────────────────────────────────────
        # If already processed, acknowledge and exit (prevents duplicate signals)
        if payment.status in ['completed', 'failed']:
            logger.info(f"M-Pesa callback received for already processed payment {payment.id}")
            return JsonResponse({"ResultCode": 0, "ResultDesc": "Success (Already Processed)"})
        # ───────────────────────────────────────────────────────────────────

        if result_code == 0:
            # Success! Extract Receipt Number
            callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            receipt_number = ""
            for item in callback_metadata:
                if item.get('Name') == 'MpesaReceiptNumber':
                    receipt_number = item.get('Value')
                    break
            
            payment.status = 'completed'
            payment.mpesa_transaction_id = receipt_number
            payment.transaction_id = receipt_number
            payment.payment_verified_at = timezone.now()
            payment.payment_date = timezone.now()
            payment.save()
            
            # The on_payment_completed signal in signals.py will handle badge/course access
            return JsonResponse({"ResultCode": 0, "ResultDesc": "Success"})
        else:
            # Failed
            payment.status = 'failed'
            payment.verification_notes = f"Safaricom Error: {stk_callback.get('ResultDesc')}"
            payment.save()
            return JsonResponse({"ResultCode": 0, "ResultDesc": "Acknowledged Failure"})

    except json.JSONDecodeError:
        logger.error("Invalid JSON in M-Pesa callback")
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid JSON"}, status=400)
    except Payment.DoesNotExist:
        logger.warning("Payment not found in M-Pesa callback")
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Payment not found"}, status=404)
    except Exception as e:
        logger.error(f"Unexpected error in M-Pesa callback: {e}", exc_info=True)
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Internal error"}, status=500)


@login_required
def check_payment_status(request, payment_id):
    """
    JSON endpoint for frontend polling
    """
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    return JsonResponse({
        'status': payment.status,
        'id': payment.id,
        'is_completed': payment.status == 'completed'
    })


@login_required
def payment_verification_submitted(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    return render(request, 'payments/verification_submitted.html', {'payment': payment})


@login_required
def payment_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    return render(request, 'payments/payment_detail.html', {'payment': payment})


@login_required
def payment_history(request):
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'payments/history.html', {'payments': payments})


@login_required
def contribution_list(request):
    """View to list all monthly contributions for a worker"""
    if request.user.user_type != 'househelp':
        return redirect('home')
        
    contributions = MonthlyContribution.objects.filter(worker=request.user).order_by('-year', '-month')
    return render(request, 'payments/contribution_list.html', {'contributions': contributions})


@login_required
def job_checkout(request, job_id):
    job = get_object_or_404(Job, id=job_id, employer=request.user)
    
    # If already paid, redirect to my jobs
    if job.posting_fee_paid:
        messages.info(request, "This job activation fee has already been paid.")
        return redirect('jobs:my_jobs')
    
    # Get the fee based on the user's current subscription
    features = UserSubscription.get_active_features(request.user)
    job_fee = features.job_posting_fee if features else 250
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        
        if not phone_number:
            messages.error(request, "Please provide a valid M-Pesa phone number.")
            return redirect('payments:job_checkout', job_id=job.id)
            
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            job=job,
            amount=job_fee,
            payment_method='mpesa',
            status='pending',
            verification_notes=f"Job Activation Fee for '{job.title}'"
        )
        
        # Professional API Flow: STK Push
        normalized_phone = normalize_kenyan_phone(phone_number)
        if not normalized_phone:
            messages.error(request, "Invalid Kenyan phone number format. Use 07... or 254...")
            return redirect('payments:job_checkout', job_id=job.id)

        client = MpesaClient()
        response = client.initiate_stk_push(
            phone_number=normalized_phone,
            amount=job_fee,
            reference_id=f"JOB{job.id}",
            description=f"Job Post Activation"
        )
        
        if response.get('success'):
            payment.stk_reference_id = response.get('checkout_request_id')
            payment.is_mpesa_stk = True
            payment.phone_number = phone_number
            payment.save()
            
            # Link payment to mpesa_payment status page
            messages.success(request, f'M-Pesa prompt sent! Complete payment of KSh {job_fee} on your phone.')
            return redirect('payments:mpesa_payment', payment_id=payment.id)
        else:
            messages.error(request, f"M-Pesa error: {response.get('message')}. Please try again.")
            
    return render(request, 'payments/job_checkout.html', {
        'job': job,
        'job_fee': job_fee,
        'features': features
    })