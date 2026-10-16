import hashlib
import hmac
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.core import mail

from .forms import CustomUserChangeForm
from .models import AgreementIssuance, CustomUser, PlatformDocument


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


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    },
)
class AccountLifecycleTests(TestCase):
    def test_signup_requires_email_verification(self):
        response = self.client.post('/accounts/signup/', {
            'first_name': 'New', 'last_name': 'User', 'email': 'new@example.com',
            'user_type': 'employer', 'phone_number': '+254711111111',
            'password1': 'A-strong-password-123', 'password2': 'A-strong-password-123',
        })
        self.assertRedirects(response, '/accounts/login/')
        user = CustomUser.objects.get(email='new@example.com')
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_page_exists(self):
        response = self.client.get('/accounts/password_reset/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reset your password')
        self.assertContains(response, 'id="id_email"')
        self.assertContains(response, 'border-pink-300')

    def test_delete_account_requires_correct_password(self):
        user = CustomUser.objects.create_user(
            username='0712345678', email='delete@example.com', phone_number='+254712345678',
            user_type='employer', password='correct-password', is_active=True,
        )
        self.client.force_login(user)
        response = self.client.post('/accounts/delete-account/', {'password': 'wrong'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CustomUser.objects.filter(pk=user.pk).exists())
        self.client.post('/accounts/delete-account/', {'password': 'correct-password'})
        self.assertFalse(CustomUser.objects.filter(pk=user.pk).exists())


@override_settings(SECRET_KEY='test-secret-key')
class AgreementFlowTests(TestCase):
    def setUp(self):
        self.worker = CustomUser.objects.create_user(
            username='0712345678',
            email='worker@example.com',
            phone_number='+254712345678',
            user_type='househelp',
            first_name='Test',
            last_name='Worker',
            county='Nairobi',
            constituency='Westlands',
            major_town='Parklands',
            ward='Highridge',
            password='password',
        )
        self.employer = CustomUser.objects.create_user(
            username='0798765432',
            email='employer@example.com',
            phone_number='+254798765432',
            user_type='employer',
            password='password',
        )

        self.document = PlatformDocument.objects.create(
            name='Worker agreement',
            doc_type='worker_agreement',
            is_active=True,
        )
        self.document.document_file.save(
            'agreement.pdf',
            SimpleUploadedFile('agreement.pdf', b'%PDF-1.4 agreement'),
            save=True,
        )

    def test_only_housekeepers_can_download_and_download_creates_issuance(self):
        self.client.force_login(self.employer)
        response = self.client.get('/dashboard/agreement/download/')
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.worker)
        response = self.client.get('/dashboard/agreement/download/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('CHARLADY_Househelp_Agreement_', response['Content-Disposition'])
        self.assertEqual(AgreementIssuance.objects.filter(user=self.worker).count(), 1)

    def test_signed_upload_marks_pending_issuance_submitted(self):
        AgreementIssuance.objects.create(
            user=self.worker,
            agreement_id='CL-HHA-ABC234',
            status='pending',
        )
        self.client.force_login(self.worker)
        response = self.client.post(
            '/accounts/edit-profile/',
            data={
                'first_name': 'Test',
                'last_name': 'Worker',
                'email': 'worker@example.com',
                'user_type': 'househelp',
                'phone_number': '+254712345678',
                'county': 'Nairobi',
                'constituency': 'Westlands',
                'major_town': 'Parklands',
                'ward': 'Highridge',
                'agreement_form': SimpleUploadedFile(
                    'signed.pdf', b'%PDF-1.4 signed agreement', content_type='application/pdf'
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        issuance = AgreementIssuance.objects.get(user=self.worker)
        self.assertEqual(issuance.status, 'submitted')
        self.assertIsNotNone(issuance.submitted_at)

    def test_agreement_upload_rejects_unsupported_files(self):
        form = CustomUserChangeForm(
            data={
                'first_name': 'Test',
                'last_name': 'Worker',
                'email': 'worker@example.com',
                'user_type': 'househelp',
                'phone_number': '+254712345678',
                'county': 'Nairobi',
                'constituency': 'Westlands',
                'major_town': 'Parklands',
                'ward': 'Highridge',
            },
            files={'agreement_form': SimpleUploadedFile('signed.exe', b'bad', content_type='application/octet-stream')},
            instance=self.worker,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('agreement_form', form.errors)