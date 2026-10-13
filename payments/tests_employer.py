from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from accounts.models import CustomUser
from .models import PaymentPlan, UserSubscription


class EmployerPrivilegeTests(TestCase):
    def setUp(self):
        cache.clear()
        self.employer = CustomUser.objects.create_user(
            username='0798765432',
            email='employer@example.com',
            phone_number='+254798765432',
            user_type='employer',
            password='password',
        )
        self.free_plan = PaymentPlan.objects.create(
            name='Free Tier',
            plan_type='verification',
            target_group='employer',
            price=0,
            description='Free',
            job_posting_fee=250,
            can_use_video=False,
            chat_conversation_limit=2,
            chat_message_limit=5,
        )
        self.gold_plan = PaymentPlan.objects.create(
            name='Gold Plan',
            plan_type='verification',
            target_group='employer',
            price=350,
            description='Gold',
            job_posting_fee=0,
            can_use_video=True,
            video_call_limit_mins=0,
            chat_conversation_limit=0,
            chat_message_limit=0,
        )

    def test_multiple_employer_tiers_can_coexist(self):
        self.assertEqual(PaymentPlan.objects.filter(target_group='employer').count(), 2)

    def test_free_tier_limits_are_returned_without_subscription(self):
        features = UserSubscription.get_active_features(self.employer)

        self.assertEqual(features.name, 'Free Tier')
        self.assertEqual(features.chat_conversation_limit, 2)
        self.assertFalse(features.can_use_video)

    def test_expired_cached_subscription_falls_back_to_free_tier(self):
        UserSubscription.objects.create(
            user=self.employer,
            plan=self.gold_plan,
            status='active',
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        features = UserSubscription.get_active_features(self.employer)

        self.assertEqual(features.name, 'Free Tier')
        self.assertFalse(features.can_use_video)