import os
import django

# Set up the Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housekeeper_connect.settings')
django.setup()

from accounts.models import CustomUser
from payments.models import PaymentPlan

# Admin user creation removed per request since you've successfully created it!

# 2. Create the Standard Plan (300 KES)
standard_plan, s_created = PaymentPlan.objects.get_or_create(
    price=300,
    defaults={
        'name': 'Standard Plan',
        'plan_type': 'verification',
        'description': 'Verified status, discounted job posts, and 15-minute HD video interviews with workers.',
        'duration_days': 30,
        'is_active': True
    }
)
if s_created:
    print("Standard Plan (300 KES) created successfully!")
else:
    print("Standard Plan (300 KES) already exists. Skipping.")

# 3. Create the Pro Plan (1000 KES)
pro_plan, p_created = PaymentPlan.objects.get_or_create(
    price=1000,
    defaults={
        'name': 'Gold Plan',
        'plan_type': 'verification',
        'description': 'Unlimited job postings, priority matching, and unlimited HD video interviewing with all talent.',
        'duration_days': 30,
        'is_active': True
    }
)
if p_created:
    print("Gold Plan (1000 KES) created successfully!")
else:
    # Update existing Pro plan to Gold branding
    pro_plan.name = "Gold Plan"
    pro_plan.description = "Unlimited job postings, priority matching, and unlimited HD video interviewing with all talent."
    pro_plan.save()
    print("Gold Plan (1000 KES) branding updated.")
