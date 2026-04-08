from django.test import Client, SimpleTestCase


class GameViewTests(SimpleTestCase):
    def test_home_returns_ok_and_contains_assets_array(self):
        response = Client().get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'const cardPaths = [')
        self.assertContains(response, 'assets/card/')
        self.assertContains(response, 'const handbookData =')
        self.assertContains(response, '图鉴 handbook')

    def test_handbook_page_renders_and_has_type_tabs(self):
        response = Client().get('/handbook/?type=spell&page=1')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '图鉴 /handbook')
        self.assertContains(response, '/handbook/?type=card&page=1')
        self.assertContains(response, '/handbook/?type=spell&page=1')
        self.assertContains(response, '/handbook/?type=weapon&page=1')
