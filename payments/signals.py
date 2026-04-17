"""
Django signals for payment completion and related actions
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Payment, UserSubscription, MonthlyContribution
from notifications.utils import create_notification

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Payment)
def on_payment_completed(sender, instance, created, update_fields, **kwargs):
    """
    Signal handler: When payment status changes to 'completed'
    - Grant membership badge to workers
    - Create/update employer subscription
    - Update monthly contribution status
    """
    
    # Only process when status changes to 'completed'
    if instance.status != 'completed':
        return
    
    if not instance.payment_date:
        instance.payment_date = timezone.now()
        instance.save(update_fields=['payment_date'])

    user = instance.user

    # ─── WORKER PAYMENTS (250 KES membership or contributions) ───────────────
    if user.user_type == 'househelp':
        
        # Case 1: 250 KES annual membership
        if instance.plan and instance.plan.plan_type == 'verification' and float(instance.amount) == 250:
            logger.info(f"Granting membership badge to worker {user.username}")
            
            # Grant membership badge
            user.is_paid_verified = True
            user.paid_verification_date = timezone.now()
            user.paid_verification_expires_at = timezone.now() + timedelta(days=365)
            user.save()
            
            # Notify user
            create_notification(
                recipient=user,
                notification_type='system',
                title='✓ Verification Complete!',
                message='Your membership has been activated. You now have the verified badge and can apply for more jobs!',
                related_object=instance
            )
            
            # Notify admins
            from django.contrib.auth import get_user_model
            for admin in get_user_model().objects.filter(is_staff=True):
                create_notification(
                    recipient=admin,
                    notification_type='system',
                    title='New Worker Verification',
                    message=f'{user.get_full_name or user.username} verified as member.',
                    related_object=instance
                )
        
        # Case 2: Monthly 3% contribution payment
        elif instance.plan and instance.plan.plan_type == 'monthly_contribution':
            logger.info(f"Recording 3% contribution payment for {user.username}")
            
            # Find and update the corresponding MonthlyContribution
            from datetime import date
            today = date.today()
            
            contribution = MonthlyContribution.objects.filter(
                worker=user,
                year=today.year,
                month=today.month,
                payment_status='pending'
            ).first()
            
            if contribution:
                contribution.payment_status = 'paid'
                contribution.payment_date = timezone.now()
                contribution.mpesa_transaction_id = instance.mpesa_transaction_id
                contribution.save()
                
                logger.info(f"Updated contribution for {user.username}: {contribution}")
                
                # Notify worker
                create_notification(
                    recipient=user,
                    notification_type='system',
                    title='✓ Contribution Received',
                    message=f'Your KES {float(contribution.amount_due):.2f} monthly contribution has been received. Thank you for supporting Charlady!',
                    related_object=contribution
                )
        
        # Case 3: Course payment
        elif instance.course:
            logger.info(f"Recording course enrollment for {user.username}: {instance.course.title}")
            
            from courses.models import CourseCompletion
            # Mark user as having access/completed the course
            # (In real scenario, you'd have an Enrollment model tracking progress)
            CourseCompletion.objects.get_or_create(user=user, course=instance.course)
            
            create_notification(
                recipient=user,
                notification_type='system',
                title='✓ Course Access Granted',
                message=f'You now have access to {instance.course.title}. Start learning!',
                related_object=instance.course
            )

    # ─── EMPLOYER PAYMENTS (Subscription plans) ─────────────────────────────
    elif user.user_type == 'employer':
        
        if instance.plan:
            logger.info(f"Creating/updating subscription for employer {user.username}: {instance.plan.name}")
            
            # Calculate expiry date (based on plan duration_days)
            expires_at = timezone.now() + timedelta(days=instance.plan.duration_days)
            
            # Get or create subscription
            subscription, created = UserSubscription.objects.get_or_create(
                user=user,
                plan=instance.plan,
                defaults={
                    'status': 'active',
                    'expires_at': expires_at
                }
            )
            
            if not created:
                # Update existing subscription
                subscription.status = 'active'
                subscription.expires_at = expires_at
                subscription.save()
                logger.info(f"Updated existing subscription for {user.username}")
            
            # --- FEATURE: Grant Verified Badge to Paid Employers ---
            if instance.plan.price >= 150:
                user.is_verified = True
                user.save(update_fields=['is_verified'])
                logger.info(f"Granted Verified Badge to Employer {user.username} (Price: {instance.plan.price})")
            
            # Notify employer
            create_notification(
                recipient=user,
                notification_type='system',
                title='✓ Subscription Activated!',
                message=f'You are now on the {subscription.get_tier_name()} plan. Enjoy premium features!',
                related_object=subscription
            )

    # ─── JOB ACTIVATION PAYMENTS ──────────────────────────────────────────
    if instance.job:
        logger.info(f"Activating job '{instance.job.title}' after payment {instance.id}")
        job = instance.job
        job.is_active = True
        job.posting_fee_paid = True
        job.save()

        # Notify employer
        create_notification(
            recipient=user,
            notification_type='system',
            title='✓ Job Activated!',
            message=f'Your job post "{job.title}" is now live and visible to all workers.',
            related_object=job
        )


def check_expired_memberships():
    """
    Task to check and notify workers about expiring memberships
    Run daily or on-demand
    """
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    
    User = get_user_model()
    
    # Find memberships expiring in 2 weeks
    expiry_threshold = timezone.now() + timedelta(days=14)
    
    soon_to_expire = User.objects.filter(
        is_paid_verified=True,
        paid_verification_expires_at__lt=expiry_threshold,
        paid_verification_expires_at__gt=timezone.now()
    )
    
    for user in soon_to_expire:
        # Check if we already sent reminder this month
        if user.last_reminder_sent and timezone.now() - user.last_reminder_sent < timedelta(days=7):
            continue
        
        days_left = user.days_until_membership_renewal()
        
        create_notification(
            recipient=user,
            notification_type='system',
            title=f'Membership Expiring Soon ({days_left} days)',
            message=f'Your verification membership expires in {days_left} days. Renew now to maintain your verified status!',
        )
        
        user.last_reminder_sent = timezone.now()
        user.save()
        
        logger.info(f"Sent renewal reminder to {user.username} (days left: {days_left})")


def check_expired_subscriptions():
    """
    Task to check and mark expired employer subscriptions
    Run daily or on-demand
    """
    from django.utils import timezone
    
    # Mark expired subscriptions
    UserSubscription.objects.filter(
        status='active',
        expires_at__lt=timezone.now()
    ).update(status='expired')
    
    logger.info("Checked and updated expired subscriptions")
