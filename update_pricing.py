import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'housekeeper_connect.settings')
django.setup()

from payments.models import PaymentPlan

def update_pricing():
    # 1. Employer Free Plan (0 KES)
    free_plan, _ = PaymentPlan.objects.get_or_create(
        name='Free Tier',
        target_group='employer',
        defaults={'price': 0}
    )
    free_plan.price = 0
    free_plan.job_posting_fee = 250
    free_plan.video_call_limit_mins = 0
    free_plan.can_use_video = False
    free_plan.chat_conversation_limit = 2
    free_plan.chat_message_limit = 5
    free_plan.description = 'Basic access: 250 KES per job post. No video calls. Limited chat.'
    free_plan.save()
    print("Free Tier updated with strict limits.")

    # 2. Employer Standard Plan (150 KES)
    standard_plan, _ = PaymentPlan.objects.get_or_create(
        name='Standard Plan',
        target_group='employer',
        defaults={'price': 150}
    )
    standard_plan.price = 150
    standard_plan.job_posting_fee = 100 # Discounted
    standard_plan.video_call_limit_mins = 15
    standard_plan.can_use_video = True
    standard_plan.chat_conversation_limit = 0 # Unlimited
    standard_plan.chat_message_limit = 0
    standard_plan.description = 'Premium access: 100 KES per job post. 15-minute video interviews. Verified Badge.'
    standard_plan.save()
    print("Standard Plan updated with 15-min video limit and 100 KES job fee.")

    # 3. Employer Gold Plan (350 KES)
    gold_plan, _ = PaymentPlan.objects.get_or_create(
        name='Gold Plan',
        target_group='employer',
        defaults={'price': 350}
    )
    gold_plan.price = 350
    gold_plan.job_posting_fee = 0 # Free
    gold_plan.video_call_limit_mins = 0 # Unlimited
    gold_plan.can_use_video = True
    gold_plan.chat_conversation_limit = 0
    gold_plan.chat_message_limit = 0
    gold_plan.description = 'Elite access: Free job posts. Unlimited video interviews. Verified Badge.'
    gold_plan.save()
    print("Gold Plan updated with Unlimited features.")

    # 4. Worker Verification (Sync)
    worker_plan = PaymentPlan.objects.filter(target_group='worker', plan_type='verification').first()
    if worker_plan:
        worker_plan.price = 250
        worker_plan.save()
        print("Worker Verification sync'd.")

if __name__ == "__main__":
    update_pricing()
