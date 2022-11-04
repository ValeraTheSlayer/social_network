from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from mixer.backend.django import mixer
from django.core.cache import cache
from posts.models import Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = mixer.blend('posts.Group')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.post_url = f'/posts/{cls.post.id}'
        cls.post_edit_url = f'/posts/{cls.post.id}/edit/'
        cls.public_url = (
            ('/', 'posts/index.html'),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{cls.user.username}/', 'posts/profile.html'),
            (f'/posts/{cls.post.id}/', 'posts/post_detail.html'),
        )
        cls.private_url = (
            ('/create/', 'posts/create_post.html'),
            (f'/posts/{cls.post.id}/edit/', 'posts/create_post.html'),
        )

    def setUp(self):
        cache.clear()

    def test_public_urls_exist_at_desired_location(self):
        for url, template in self.public_url:
            with self.subTest(template=template):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_private_url_exists_at_desired_location(self):
        for url, template in self.private_url:
            with self.subTest(template=template):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def unexisting_page_exist_at_desired_location(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)

    def unexisting_page_uses_correct_template(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'posts/core/404.html')

    def test_create_edit_post_url_redirect_anonymous_on_admin_login(self):
        create_edit_post = {
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{self.post.id}/edit/': (
                f'/auth/login/?next=/posts/{self.post.id}/edit/'
            ),
        }
        for url, redirect in create_edit_post.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect)

    def test_public_urls_uses_correct_template(self):
        for url, template in self.public_url:
            with self.subTest(template=template):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
                cache.clear()

    def test_private_urls_uses_correct_template(self):
        for url, template in self.private_url:
            with self.subTest(template=template):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
