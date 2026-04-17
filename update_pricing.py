import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housekeeper_connect.settings')
django.setup()

from payments.models import PaymentPlan

def update_pricing():
    # 1. Employer Free Plan
    free_plan, _ = PaymentPlan.objects.get_or_create(
        name='Free Tier',
        target_group='employer',
        defaults={
            'price': 0,
            'plan_type': 'verification',
            'description': 'Browse workers, view profiles, and post basic job listings.',
            'duration_days': 365,
            'is_active': True
        }
    )
    free_plan.price = 0
    free_plan.save()
    print("Free Tier updated.")

    # 2. Employer Standard Plan (150 KES)
    standard_plan = PaymentPlan.objects.filter(name='Standard Plan', target_group='employer').first()
    if standard_plan:
        standard_plan.price = 150
        standard_plan.description = 'Verified status (Blue Badge), discounted job posts, and 15-min HD video interviews.'
        standard_plan.save()
        print("Standard Plan updated to 150 KES.")
    else:
        PaymentPlan.objects.create(
            name='Standard Plan',
            price=150,
            target_group='employer',
            plan_type='verification',
            description='Verified status (Blue Badge), discounted job posts, and 15-min HD video interviews.',
            duration_days=30,
            is_active=True
        )
        print("Standard Plan created at 150 KES.")

    # 3. Employer Gold Plan (350 KES)
    gold_plan = PaymentPlan.objects.filter(name='Gold Plan', target_group='employer').first()
    if gold_plan:
        gold_plan.price = 350
        gold_plan.description = 'Unlimited postings, Verified Badge (Blue Badge), and unlimited HD video interviews.'
        gold_plan.save()
        print("Gold Plan updated to 350 KES.")
    else:
        PaymentPlan.objects.create(
            name='Gold Plan',
            price=350,
            target_group='employer',
            plan_type='verification',
            description='Unlimited postings, Verified Badge (Blue Badge), and unlimited HD video interviews.',
            duration_days=30,
            is_active=True
        )
        print("Gold Plan created at 350 KES.")

    # 4. Worker Verification (Sync to 250)
    worker_plan = PaymentPlan.objects.filter(target_group='worker', plan_type='verification').first()
    if worker_plan:
        worker_plan.price = 250
        worker_plan.save()
        print("Worker Verification updated to 250 KES.")

if __name__ == "__main__":
    update_pricing()
