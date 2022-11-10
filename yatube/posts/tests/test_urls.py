from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.views import redirect_to_login
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from mixer.backend.django import mixer

from posts.models import Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user, cls.author_user = mixer.cycle(2).blend(
            User,
            username=(name for name in ('user', 'author-user')),
        )
        cls.anon = Client()
        cls.auth = Client()
        cls.auth.force_login(cls.user)
        cls.auth_author = Client()
        cls.auth_author.force_login(cls.author_user)
        cls.group = mixer.blend('posts.Group')
        cls.post = Post.objects.create(
            author=cls.author_user,
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
                response = self.anon.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_url_exists_at_desired_location(self):
        for url, template in self.private_url:
            with self.subTest(template=template):
                response = self.auth_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def unexisting_page_exist_at_desired_location(self):
        response = self.anon.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def unexisting_page_uses_correct_template(self):
        response = self.anon.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'posts/core/404.html')

    def test_create_edit_post_url_redirect_anonymous_on_admin_login(self):
        create_edit_post = {
            '/create/': redirect_to_login(
                reverse('posts:post_create'),
            ).url,
            f'/posts/{self.post.id}/edit/': redirect_to_login(
                reverse(
                    'posts:post_edit',
                    args=(self.post.id,),
                ),
            ).url,
        }
        for url, redirect in create_edit_post.items():
            with self.subTest(url=url):
                response = self.anon.get(url, follow=True)
                self.assertRedirects(response, redirect)

    def test_edit_post_url_redirect_not_author_on_post_detail(self):
        self.assertRedirects(
            self.auth.get(f'/posts/{self.post.id}/edit/', follow=True),
            f'/posts/{self.post.id}/',
        )

    def test_public_urls_uses_correct_template(self):
        for url, template in self.public_url:
            with self.subTest(template=template):
                response = self.anon.get(url)
                self.assertTemplateUsed(response, template)

    def test_private_urls_uses_correct_template(self):
        for url, template in self.private_url:
            with self.subTest(template=template):
                response = self.auth_author.get(url)
                self.assertTemplateUsed(response, template)
