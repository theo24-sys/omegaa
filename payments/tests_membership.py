from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import CustomUser
from .tasks import expire_paid_memberships


class MembershipExpiryTests(TestCase):
    def test_expired_paid_membership_loses_paid_badge(self):
        user = CustomUser.objects.create_user(
            username='0712345678',
            email='worker@example.com',
            phone_number='+254712345678',
            user_type='househelp',
            password='password',
            is_paid_verified=True,
            paid_verification_expires_at=timezone.now() - timedelta(minutes=1),
        )

        result = expire_paid_memberships.apply().get()

        user.refresh_from_db()
        self.assertEqual(result, 1)
        self.assertFalse(user.is_paid_verified)