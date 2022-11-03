from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from users.forms import CreationForm

User = get_user_model()


class CreationFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = CreationForm()
        cls.guest_client = Client()

    def test_signup(self):
        self.assertEqual(User.objects.count(), 0)
        response = self.guest_client.post(
            reverse('users:signup'),
            data={
                'first_name': 'test_first_name',
                'last_name': 'test_last_name',
                'username': 'test_name',
                'email': 'email_test@mail.ru',
                'password1': 'Django_2022',
                'password2': 'Django_2022',
            },
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(User.objects.filter(username='test_name').exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)
