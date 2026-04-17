import os
import django

# Set up the Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housekeeper_connect.settings')
django.setup()

from accounts.models import CustomUser
from payments.models import PaymentPlan

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
standard_plan = PaymentPlan.objects.filter(name='Standard Plan').first()
if not standard_plan:
    standard_plan = PaymentPlan.objects.create(
        name='Standard Plan',
        price=150,
        job_posting_fee=150,
        plan_type='verification',
        description='Standard status, discounted job posts, and 15-minute HD video interviews.',
        duration_days=30,
        is_active=True,
        target_group='employer'
    )
else:
    standard_plan.price = 150
    standard_plan.job_posting_fee = 150
    standard_plan.description = 'Standard status, discounted job posts, and 15-minute HD video interviews.'
    standard_plan.save()
print("Standard Plan (150 KES) synced.")

# 3. Sync Gold Plan (350 KES Subscription, FREE Job Fee)
gold_plan = PaymentPlan.objects.filter(name='Gold Plan').first()
if not gold_plan:
    gold_plan = PaymentPlan.objects.create(
        name='Gold Plan',
        price=350,
        job_posting_fee=0,
        plan_type='verification',
        description="Unlimited job postings, priority matching, and unlimited HD video interviewing.",
        duration_days=30,
        is_active=True,
        target_group='employer'
    )
else:
    gold_plan.price = 350
    gold_plan.job_posting_fee = 0
    gold_plan.description = "Unlimited job postings, priority matching, and unlimited HD video interviewing."
    gold_plan.save()
print("Gold Plan (350 KES) synced.")

# 4. Sync Worker Verification (250 KES)
worker_plan = PaymentPlan.objects.filter(name='Worker Verification', target_group='worker').first()
if not worker_plan:
    worker_plan = PaymentPlan.objects.create(
        name='Worker Verification',
        price=250,
        target_group='worker',
        plan_type='verification',
        description='Get the "Verified" badge, unlimited applications, and priority placement.',
        duration_days=365,
        is_active=True
    )
else:
    worker_plan.price = 250
    worker_plan.save()
print("Worker Verification (250 KES) synced.")
