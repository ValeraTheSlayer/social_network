from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class UserURLTests(TestCase):
    def setUp(self):
        self.anon = Client()

    def test_signup_url_exists_at_desired_location(self):
        response = self.anon.get('/auth/signup/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        response = self.anon.get('/auth/signup/')
        self.assertTemplateUsed(response, 'users/signup.html')
