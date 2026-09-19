from django.test import SimpleTestCase

from housekeeper_connect import settings as app_settings


class MpesaSettingsAliasTests(SimpleTestCase):
    def test_sandbox_aliases_are_used_when_env_is_sandbox(self):
        values = app_settings.resolve_mpesa_settings(
            environment='sandbox',
            env={
                'MPESA_CONSUMER_KEY_SANDBOX': 'sandbox_key',
                'MPESA_CONSUMER_SECRET_SANDBOX': 'sandbox_secret',
                'MPESA_PASSKEY_SANDBOX': 'sandbox_passkey',
                'MPESA_SHORT_CODE_SANDBOX': '123456',
            },
        )

        self.assertEqual(values['consumer_key'], 'sandbox_key')
        self.assertEqual(values['consumer_secret'], 'sandbox_secret')
        self.assertEqual(values['passkey'], 'sandbox_passkey')
        self.assertEqual(values['short_code'], '123456')

    def test_production_aliases_are_used_when_env_is_production(self):
        values = app_settings.resolve_mpesa_settings(
            environment='production',
            env={
                'MPESA_CONSUMER_KEY_PRODUCTION': 'prod_key',
                'MPESA_CONSUMER_SECRET_PRODUCTION': 'prod_secret',
                'MPESA_PASSKEY_PRODUCTION': 'prod_passkey',
                'MPESA_SHORT_CODE_PRODUCTION': '654321',
            },
        )

        self.assertEqual(values['consumer_key'], 'prod_key')
        self.assertEqual(values['consumer_secret'], 'prod_secret')
        self.assertEqual(values['passkey'], 'prod_passkey')
        self.assertEqual(values['short_code'], '654321')

    def test_primary_keys_override_aliases(self):
        values = app_settings.resolve_mpesa_settings(
            environment='sandbox',
            env={
                'MPESA_CONSUMER_KEY': 'primary_key',
                'MPESA_CONSUMER_KEY_SANDBOX': 'alias_key',
                'MPESA_CONSUMER_SECRET': 'primary_secret',
                'MPESA_CONSUMER_SECRET_SANDBOX': 'alias_secret',
                'MPESA_PASSKEY': 'primary_passkey',
                'MPESA_PASSKEY_SANDBOX': 'alias_passkey',
                'MPESA_SHORT_CODE': 'primary_short_code',
                'MPESA_SHORT_CODE_SANDBOX': 'alias_short_code',
            },
        )

        self.assertEqual(values['consumer_key'], 'primary_key')
        self.assertEqual(values['consumer_secret'], 'primary_secret')
        self.assertEqual(values['passkey'], 'primary_passkey')
        self.assertEqual(values['short_code'], 'primary_short_code')
