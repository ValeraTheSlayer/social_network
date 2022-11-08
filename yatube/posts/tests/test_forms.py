import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.views import redirect_to_login
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from mixer.backend.django import mixer

from posts.models import Comment, Post
from posts.tests.common import image

User = get_user_model()


@override_settings(MEDIA_ROOT=settings.MEDIA_ROOT)
class PostFormTest(TestCase):
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
        cls.group = mixer.blend('posts.Group')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_create_post_without_group_assignment(self):
        response = self.auth.post(
            reverse('posts:post_create'),
            {
                'text': 'Тестовый пост',
            },
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                args=(self.user.username,),
            ),
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.get()
        self.assertEqual(post.text, 'Тестовый пост')
        self.assertEqual(post.group, None)
        self.assertEqual(post.author, self.user)

    def test_create_post_with_group_assignment(self):
        response = self.auth.post(
            reverse('posts:post_create'),
            {
                'text': 'Тестовый пост',
                'group': self.group.id,
            },
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                args=(self.user.username,),
            ),
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.get()
        self.assertEqual(post.text, 'Тестовый пост')
        self.assertEqual(post.group.id, self.group.id)
        self.assertEqual(post.author, self.user)

    def test_anon_cant_post(self):
        response = self.anon.post(
            reverse('posts:post_create'),
            {
                'text': 'Тестовый пост',
            },
            follow=True,
        )
        self.assertRedirects(
            response,
            '/auth/login/?next=/create/',
        )
        self.assertEqual(Post.objects.count(), 0)

    def test_auth_client_can_edit_own_post(self):
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый текст',
        )
        response = self.auth.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            {
                'text': 'Изменяем пост',
            },
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=(self.post.id,)),
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.get()
        self.assertEqual(post.text, 'Изменяем пост')
        self.assertEqual(post.group, None)
        self.assertEqual(post.author, self.user)

    def test_auth_client_cant_edit_another_post(self):
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.author_user,
        )
        response = self.auth.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            {
                'text': 'Изменяем пост',
            },
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=(self.post.id,)),
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.get()
        self.assertEqual(post.text, 'Тестовый текст')
        self.assertEqual(post.group, None)
        self.assertEqual(post.author.username, 'author-user')

    def test_anon_cant_edit_any_post(self):
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.author_user,
        )
        response = self.anon.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            {
                'text': 'Изменяем пост',
            },
            follow=True,
        )
        self.assertRedirects(
            response,
            redirect_to_login(
                f'/posts/{self.post.id}/edit/',
                login_url='/auth/login/',
                redirect_field_name='next',
            ).url,
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.get()
        self.assertEqual(post.text, 'Тестовый текст')
        self.assertEqual(post.group, None)
        self.assertEqual(post.author.username, 'author-user')

    def only_auth_can_comment(self):
        response = self.auth.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data={'text': 'Тестовый коммент'},
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=(self.post.id,)),
        )
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.get()
        self.assertEqual(comment.text, 'Тестовый коммент')

    def anon_cant_comment(self):
        self.anon.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            {'text': 'Тестовый коммент'},
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), 0)

    def test_create_post_ok(self):
        response = self.auth.post(
            reverse('posts:post_create'),
            {
                'text': 'Тестовый пост',
                'group': self.group.id,
                'image': image(),
            },
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', args=(self.user.username,)),
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.get()
        self.assertEqual(post.text, 'Тестовый пост')
        self.assertEqual(post.group.id, self.group.id)
        self.assertEqual(post.image, 'posts/giffy.gif')
