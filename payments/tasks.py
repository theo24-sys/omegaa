"""
Celery tasks and scheduled jobs for payments
- Calculate monthly contributions
- Check subscription expiries
- Send renewal reminders
"""
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import MonthlyContribution, UserSubscription
from jobs.models import Job, Application

logger = logging.getLogger(__name__)

User = get_user_model()


def calculate_monthly_contributions():
    """
    End-of-month task to calculate 3% contributions for all active workers
    
    Logic:
    - Find all completed jobs from previous month
    - Sum salaries per worker
    - Create MonthlyContribution records
    - Mark as 'ignored' if salary is zero
    
    Should be run on the 1st of each month (or on-demand)
    """
    from jobs.models import Application
    
    # Get previous month
    today = date.today()
    if today.month == 1:
        prev_month = 12
        prev_year = today.year - 1
    else:
        prev_month = today.month - 1
        prev_year = today.year
    
    logger.info(f"Calculating contributions for {prev_month}/{prev_year}")
    
    # Find all workers with completed jobs in previous month
    completed_applications = Application.objects.filter(
        status='accepted',
        updated_at__month=prev_month,
        updated_at__year=prev_year,
        applicant__user_type='househelp'
    ).select_related('job', 'applicant')
    
    # Group by applicant and sum salaries
    worker_salaries = {}
    for app in completed_applications:
        worker_id = app.applicant.id
        salary = float(app.job.salary)
        
        if worker_id not in worker_salaries:
            worker_salaries[worker_id] = Decimal('0')
        
        worker_salaries[worker_id] += Decimal(str(salary))
    
    # Create MonthlyContribution records
    created_count = 0
    ignored_count = 0
    
    for worker_id, total_salary in worker_salaries.items():
        worker = User.objects.get(id=worker_id)
        
        # Calculate 3%
        amount_due = total_salary * Decimal('0.03')
        
        if amount_due > 0:
            contribution, created = MonthlyContribution.objects.get_or_create(
                worker=worker,
                year=prev_year,
                month=prev_month,
                defaults={
                    'calculated_salary': total_salary,
                    'amount_due': amount_due,
                    'payment_status': 'pending'
                }
            )
            if created:
                created_count += 1
                logger.info(f"Created contribution for {worker.username}: KES {amount_due}")
        else:
            # Mark as ignored - no jobs/salary
            contribution, created = MonthlyContribution.objects.get_or_create(
                worker=worker,
                year=prev_year,
                month=prev_month,
                defaults={
                    'calculated_salary': Decimal('0'),
                    'amount_due': Decimal('0'),
                    'payment_status': 'ignored'
                }
            )
            if created:
                ignored_count += 1
    
    logger.info(f"Contribution calculation done: {created_count} created, {ignored_count} ignored")
    return created_count, ignored_count


def check_subscription_expiries():
    """
    Check and expire employer subscriptions that have passed their expiry date
    Run daily
    """
    logger.info("Checking subscription expiries...")
    
    expired_count = UserSubscription.objects.filter(
        status='active',
        expires_at__lt=timezone.now()
    ).update(status='expired')
    
    logger.info(f"Marked {expired_count} subscriptions as expired")
    return expired_count


def send_membership_renewal_reminders():
    """
    Send notifications to workers about expiring memberships
    Target: 2 weeks before expiry
    Run daily
    """
    from notifications.utils import create_notification
    
    logger.info("Sending membership renewal reminders...")
    
    # Find memberships expiring in 14 days
    threshold_date = timezone.now() + timedelta(days=14)
    
    soon_to_expire = User.objects.filter(
        is_paid_verified=True,
        paid_verification_expires_at__lt=threshold_date,
        paid_verification_expires_at__gt=timezone.now(),
        user_type='househelp'
    )
    
    sent_count = 0
    for worker in soon_to_expire:
        # Check if we already sent reminder this month
        if worker.last_reminder_sent and timezone.now() - worker.last_reminder_sent < timedelta(days=7):
            continue
        
        days_left = worker.days_until_membership_renewal()
        
        create_notification(
            recipient=worker,
            notification_type='system',
            title=f'Membership Expiring Soon ({days_left} days)',
            message=f'Your verification membership expires in {days_left} days. Renew now to maintain your verified badge and access to premium features.'
        )
        
        worker.last_reminder_sent = timezone.now()
        worker.save(update_fields=['last_reminder_sent'])
        
        sent_count += 1
        logger.info(f"Sent reminder to {worker.username} (days left: {days_left})")
    
    logger.info(f"Membership reminder task complete: {sent_count} reminders sent")
    return sent_count


def mark_overdue_contributions():
    """
    Task to flag overdue contribution payments
    Technically handled by MonthlyContribution.is_overdue property
    But this can be used for sending notifications
    Run daily
    """
    logger.info("Checking for overdue contributions...")
    
    # Get all pending contributions from past months
    today = date.today()
    overdue = MonthlyContribution.objects.filter(
        payment_status='pending'
    ).exclude(
        year=today.year,
        month=today.month
    )
    
    from notifications.utils import create_notification
    
    sent_count = 0
    for contribution in overdue:
        # Check if we haven't already notified (optional)
        create_notification(
            recipient=contribution.worker,
            notification_type='system',
            title=f'Overdue Contribution - {contribution.month}/{contribution.year}',
            message=f'Your KES {float(contribution.amount_due):.2f} contribution for {contribution.month}/{contribution.year} is now overdue. Please pay at your earliest convenience.'
        )
        sent_count += 1
    
    logger.info(f"Overdue contribution check complete: {sent_count} notifications sent")
    return sent_count


# ─── Optional: Celery Task Definitions (if Celery is configured) ────────────

try:
    from celery import shared_task
    
    @shared_task(bind=True)
    def calculate_monthly_contributions_task(self):
        """Celery task wrapper"""
        return calculate_monthly_contributions()
    
    @shared_task(bind=True)
    def check_subscription_expiries_task(self):
        """Celery task wrapper"""
        return check_subscription_expiries()
    
    @shared_task(bind=True)
    def send_membership_renewal_reminders_task(self):
        """Celery task wrapper"""
        return send_membership_renewal_reminders()
    
    @shared_task(bind=True)
    def mark_overdue_contributions_task(self):
        """Celery task wrapper"""
        return mark_overdue_contributions()

except ImportError:
    logger.warning("Celery not configured - tasks must be run manually or via Django management commands")
