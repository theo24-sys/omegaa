from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import PaymentPlan, Payment
from courses.models import Course
from notifications.utils import create_notification

@login_required
def payment_plans(request):
    user_type = getattr(request.user, 'user_type', 'employer')
    
    if user_type == 'househelp':
        worker_plans = PaymentPlan.objects.filter(target_group='worker', is_active=True).order_by('price')
        return render(request, 'payments/worker_plans.html', {
            'plans': worker_plans
        })
    else:
        standard_plan = PaymentPlan.objects.filter(target_group='employer', price=300, is_active=True).first()
        pro_plan = PaymentPlan.objects.filter(target_group='employer', price=1000, is_active=True).first()
        return render(request, 'payments/plans.html', {
            'standard_plan': standard_plan,
            'pro_plan': pro_plan
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
def mpesa_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user, status='pending')

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

        # Notify user
        create_notification(
            recipient=request.user,
            notification_type='system',
            title='Payment Submitted',
            message=f'Your {payment.plan.name} payment is pending verification.',
            related_object=payment
        )

        # Notify admins
        from django.contrib.auth import get_user_model
        for admin in get_user_model().objects.filter(is_staff=True):
            create_notification(
                recipient=admin,
                notification_type='system',
                title='New Payment to Verify',
                message=f'User {payment.user.username} submitted payment for {payment.plan.name}.',
                related_object=payment
            )

        messages.success(request, 'Payment details submitted. We will verify shortly.')
        return redirect('payments:payment_verification_submitted', payment_id=payment.id)

    return render(request, 'payments/mpesa_payment.html', {
        'payment': payment,
        'till_number': '4567052',
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