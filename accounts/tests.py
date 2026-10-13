import hashlib
import hmac
import json

from django.test import TestCase, override_settings

from .models import CustomUser


class DiditWebhookTests(TestCase):
    @override_settings(SECRET_KEY='test-secret-key', DIDIT_WEBHOOK_SECRET='test-secret')
    def test_missing_signature_is_rejected(self):
        response = self.client.post(
            '/accounts/didit/webhook/',
            data=json.dumps({'status': 'SUCCESS', 'vendor_data': '1'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 401)

    @override_settings(SECRET_KEY='test-secret-key', DIDIT_WEBHOOK_SECRET='test-secret')
    def test_valid_signature_marks_identity_verified(self):
        user = CustomUser.objects.create_user(
            username='0712345678',
            email='worker@example.com',
            phone_number='+254712345678',
            user_type='househelp',
            password='password',
        )
        payload = json.dumps({
            'status': 'SUCCESS',
            'vendor_data': str(user.id),
            'id': 'didit-session-1',
        }).encode()
        signature = hmac.new(b'test-secret', payload, hashlib.sha256).hexdigest()

        response = self.client.post(
            '/accounts/didit/webhook/',
            data=payload,
            content_type='application/json',
            HTTP_X_DIDIT_SIGNATURE=signature,
        )

        user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(user.is_identity_verified)
        self.assertTrue(user.badge_verified_id)