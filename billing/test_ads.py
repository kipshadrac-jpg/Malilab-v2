from django.test import TestCase, override_settings


@override_settings(SECURE_SSL_REDIRECT=False)
class AppAdsTests(TestCase):
    def test_file_is_served_as_plain_text(self):
        r = self.client.get('/app-ads.txt')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r['Content-Type'].startswith('text/plain'))
        self.assertIn('pub-4769800577067926', r.content.decode())
