"""
Celery Beat Configuration for Charlady
Scheduled tasks for monthly contributions, reminders, and maintenance
"""

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

app = Celery('housekeeper_connect')

# TaskRouter configuration
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# ============================================================================
# CELERY BEAT SCHEDULE
# ============================================================================
# Runs monthly contribution calculations and reminders

app.conf.beat_schedule = {
    # Calculate monthly contributions on 1st of each month at 00:00 UTC
    'calculate-monthly-contributions': {
        'task': 'payments.tasks.calculate_monthly_contributions',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),
        'options': {'queue': 'default', 'expires': 3600},
        'kwargs': {}
    },
    
    # Send contribution reminders on 3rd of month (3 days after calculation)
    'send-contribution-reminders': {
        'task': 'payments.tasks.send_contribution_reminders',
        'schedule': crontab(day_of_month=3, hour=9, minute=0),  # 9 AM
        'options': {'queue': 'default', 'expires': 3600},
        'kwargs': {}
    },
    
    # Check for membership expiry every day at 11:00 PM UTC
    'check-membership-expiry': {
        'task': 'payments.tasks.check_membership_expiry',
        'schedule': crontab(hour=23, minute=0),  # Daily at 11 PM
        'options': {'queue': 'default', 'expires': 3600},
        'kwargs': {}
    },
    
    # Send membership renewal reminders on 10th-20th of month (2 weeks before expiry)
    'send-membership-renewal-reminder': {
        'task': 'payments.tasks.send_membership_renewal_reminder',
        'schedule': crontab(day_of_month='10-20', hour=10, minute=0),
        'options': {'queue': 'default', 'expires': 3600},
        'kwargs': {}
    },
}

# ============================================================================
# CELERY CONFIGURATION
# ============================================================================

# Broker and backend
CELERY_BROKER_URL = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = getattr(settings, 'CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Task configuration
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'Africa/Nairobi'
CELERY_ENABLE_UTC = True

# Task execution
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# Result configuration
CELERY_RESULT_EXPIRES = 3600  # 1 hour

# ============================================================================
# STARTUP MESSAGE
# ============================================================================

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

if __name__ == '__main__':
    print("CELERY BEAT CONFIGURATION")
    print("=" * 70)
    print("\nScheduled Tasks:")
    for task_name, task_config in app.conf.beat_schedule.items():
        print(f"  • {task_name}")
        print(f"    Task: {task_config['task']}")
        print(f"    Schedule: {task_config['schedule']}")
    print("\n" + "=" * 70)
    print("\nTo start Celery Beat:")
    print("  celery -A housekeeper_connect beat -l info")
    print("\nTo start Celery Worker:")
    print("  celery -A housekeeper_connect worker -l info")
    print("\nTo monitor tasks:")
    print("  celery -A housekeeper_connect events")
    print("=" * 70)
