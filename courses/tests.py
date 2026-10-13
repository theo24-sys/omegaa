from django.test import TestCase, override_settings

from accounts.models import CustomUser
from .models import Course, CourseCompletion


@override_settings(SECRET_KEY='test-secret-key')
class CourseBadgeTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='0712345678',
            email='worker@example.com',
            phone_number='+254712345678',
            user_type='househelp',
            password='password',
            is_identity_verified=True,
        )
        self.course = Course.objects.create(
            title='Childcare Certification',
            description='Test course',
            iframe_url='https://example.com/course',
            is_free=True,
            badge_key='childcare',
        )

    def test_completion_grants_configured_badge_only(self):
        self.client.force_login(self.user)

        response = self.client.post(f'/courses/{self.course.id}/complete/')

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.badge_childcare)
        self.assertFalse(self.user.badge_verified_id)
        self.assertTrue(CourseCompletion.objects.filter(user=self.user, course=self.course).exists())