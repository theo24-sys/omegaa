from django.test import TestCase, override_settings


@override_settings(SECRET_KEY='test-secret-key')
class HealthEndpointTests(TestCase):
    def test_health_endpoint_reports_database_status(self):
        response = self.client.get('/health/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
        self.assertEqual(response.json()['database'], 'ok')

    def test_payment_health_endpoint_reports_queue_counts(self):
        response = self.client.get('/health/payments/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')