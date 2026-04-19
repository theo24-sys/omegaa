import os
import django

# Set up the Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housekeeper_connect.settings')
django.setup()

from accounts.models import CustomUser
from payments.models import PaymentPlan
from django.db import IntegrityError

# 1. Restore/Update Admin
admin_phone = "+254700111222"
admin_user, created = CustomUser.objects.get_or_create(
    phone_number=admin_phone,
    defaults={
        'username': admin_phone,
        'first_name': 'System',
        'last_name': 'Admin',
        'email': 'admin@charlady.co.ke',
        'user_type': 'employer',
        'is_paid_verified': True,
    }
)
admin_user.set_password('Admin@2026Charlady')
admin_user.is_staff = True
admin_user.is_superuser = True
admin_user.save()
print(f"Fallback admin restored. Login with {admin_phone}")

# 2. Sync Standard Plan (150 KES Subscription, 150 KES Job Fee)
try:
    standard_plan, created = PaymentPlan.objects.get_or_create(
        plan_type='verification',
        target_group='employer',
        name='Standard Plan',
        defaults={
            'price': 150,
            'job_posting_fee': 150,
            'description': 'Standard status, discounted job posts, and 15-minute HD video interviews.',
            'duration_days': 30,
            'is_active': True,
        }
    )
    if not created:
        standard_plan.price = 150
        standard_plan.job_posting_fee = 150
        standard_plan.description = 'Standard status, discounted job posts, and 15-minute HD video interviews.'
        standard_plan.save()
    print("Standard Plan (150 KES) synced.")
except IntegrityError:
    print("Standard Plan already exists (duplicate detected).")

# 3. Sync Gold Plan (350 KES Subscription, FREE Job Fee)
try:
    gold_plan, created = PaymentPlan.objects.get_or_create(
        plan_type='verification',
        target_group='employer',
        name='Gold Plan',
        defaults={
            'price': 350,
            'job_posting_fee': 0,
            'description': "Unlimited job postings, priority matching, and unlimited HD video interviewing.",
            'duration_days': 30,
            'is_active': True,
        }
    )
    if not created:
        gold_plan.price = 350
        gold_plan.job_posting_fee = 0
        gold_plan.description = "Unlimited job postings, priority matching, and unlimited HD video interviewing."
        gold_plan.save()
    print("Gold Plan (350 KES) synced.")
except IntegrityError:
    print("Gold Plan already exists (duplicate detected).")

# 4. Sync Worker Verification (250 KES)
try:
    worker_plan, created = PaymentPlan.objects.get_or_create(
        plan_type='verification',
        target_group='worker',
        defaults={
            'name': 'Worker Verification',
            'price': 250,
            'description': 'Get the "Verified" badge, unlimited applications, and priority placement.',
            'duration_days': 365,
            'is_active': True
        }
    )
    if not created:
        worker_plan.price = 250
        worker_plan.save()
    print("Worker Verification (250 KES) synced.")
except IntegrityError:
    print("Worker Verification already exists (duplicate detected).")
