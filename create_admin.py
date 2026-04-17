import os
import django

# Set up the Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housekeeper_connect.settings')
django.setup()

from accounts.models import CustomUser
from payments.models import PaymentPlan

# Restore an Admin user for recovery
admin_phone = "+254700111222"
admin_user, created = CustomUser.objects.get_or_create(
    phone_number=admin_phone,
    defaults={
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
print(f"Fallback admin restored. Login with {admin_phone} and password 'Admin@2026Charlady'")

# 2. Create/Update the Standard Plan (300 KES)
# Use filter().first() to avoid crash if multiple exact matches exist
standard_plan = PaymentPlan.objects.filter(name='Standard Plan', price=300).first()
if not standard_plan:
    standard_plan = PaymentPlan.objects.create(
        name='Standard Plan',
        price=300,
        plan_type='verification',
        description='Verified status, discounted job posts, and 15-minute HD video interviews with workers.',
        duration_days=30,
        is_active=True,
        target_group='employer'
    )
    print("Standard Plan (300 KES) created successfully!")
else:
    # Update existing
    standard_plan.target_group = 'employer'
    standard_plan.description = 'Verified status, discounted job posts, and 15-minute HD video interviews with workers.'
    standard_plan.save()
    print("Standard Plan updated.")

# 3. Create/Update the Gold Plan (1000 KES)
pro_plan = PaymentPlan.objects.filter(name='Gold Plan', price=1000).first()
if not pro_plan:
    # Check for old 'Pro Plan' naming
    pro_plan = PaymentPlan.objects.filter(price=1000).first()
    if pro_plan:
        pro_plan.name = "Gold Plan"
    else:
        pro_plan = PaymentPlan.objects.create(
            name='Gold Plan',
            price=1000,
            plan_type='verification',
            duration_days=30,
            is_active=True,
            target_group='employer'
        )
pro_plan.target_group = 'employer'
pro_plan.description = "Unlimited job postings, priority matching, and unlimited HD video interviewing with all talent."
pro_plan.save()
print("Gold Plan (1000 KES) updated.")

# 4. Create/Update the Worker Verification Plan (300 KES)
worker_plan = PaymentPlan.objects.filter(name='Worker Verification', target_group='worker').first()
if not worker_plan:
    worker_plan = PaymentPlan.objects.create(
        name='Worker Verification',
        price=300,
        target_group='worker',
        plan_type='verification',
        description='Get the "Verified" badge, unlimited job applications, and priority profile placement.',
        duration_days=365,
        is_active=True
    )
    print("Worker Verification Plan (300 KES) created!")
else:
    worker_plan.price = 300
    worker_plan.save()
    print("Worker Verification Plan already exists.")

# 5. Create Academy Triple Bundle Plan (4,500 KES)
bundle_plan = PaymentPlan.objects.filter(name='Academy Triple Bundle', price=4500).first()
if not bundle_plan:
    bundle_plan = PaymentPlan.objects.create(
        name='Academy Triple Bundle',
        price=4500,
        plan_type='academy_bundle',
        description='Unlock all 3 professional courses (Childcare, Chef, Elderly Care) for a discounted price.',
        duration_days=365,
        is_active=True,
        target_group='worker'
    )
    print("Academy Triple Bundle (4,500 KES) created successfully!")
else:
    bundle_plan.description = 'Unlock all 3 professional courses (Childcare, Chef, Elderly Care) for a discounted price.'
    bundle_plan.save()
