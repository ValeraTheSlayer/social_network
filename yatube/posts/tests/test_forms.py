import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from mixer.backend.django import mixer

from posts.models import Comment, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = mixer.blend('posts.Group')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post_without_group_assignment(self):
        self.assertEqual(Post.objects.count(), 0)
        response = self.authorized_client.post(
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
        post = Post.objects.get(id=1)
        self.assertEqual(post.text, 'Тестовый пост')
        self.assertEqual(post.group, None)
        self.assertEqual(post.author, self.user)

    def test_create_post_with_group_assignment(self):
        self.assertEqual(Post.objects.count(), 0)
        response = self.authorized_client.post(
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
        post = Post.objects.get(id=1)
        self.assertEqual(post.text, 'Тестовый пост')
        self.assertEqual(post.group.id, self.group.id)
        self.assertEqual(post.author, self.user)

    def test_guest_client_cant_post(self):
        response = self.guest_client.post(
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
        self.assertEqual(Post.objects.count(), 0)
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый текст',
        )
        response = self.authorized_client.post(
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
        post = Post.objects.get(id=1)
        self.assertEqual(post.text, 'Изменяем пост')
        self.assertEqual(post.group, None)
        self.assertEqual(post.author, self.user)

    def test_auth_client_cant_edit_another_post(self):
        self.assertEqual(Post.objects.count(), 0)
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=User.objects.create_user(username='new_author'),
        )
        response = self.authorized_client.post(
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
        post = Post.objects.get(id=1)
        self.assertEqual(post.text, 'Тестовый текст')
        self.assertEqual(post.group, None)
        self.assertEqual(post.author.username, 'new_author')

    def test_guest_client_cant_edit_any_post(self):
        self.assertEqual(Post.objects.count(), 0)
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=User.objects.create_user(username='new_author'),
        )
        response = self.guest_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            {
                'text': 'Изменяем пост',
            },
            follow=True,
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/edit/',
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.get(id=1)
        self.assertEqual(post.text, 'Тестовый текст')
        self.assertEqual(post.group, None)
        self.assertEqual(post.author.username, 'new_author')

    def only_auth_can_comment(self):
        self.assertEqual(Comment.objects.count(), 0)
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data={'text': 'Тестовый коммент'},
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args=(self.post.id,)),
        )
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.get(id=1)
        self.assertEqual(comment.text, 'Тестовый коммент')

    def guest_client_cant_comment(self):
        self.assertEqual(Comment.objects.count(), 0)
        self.guest_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            {'text': 'Тестовый коммент'},
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), 0)

    def test_create_post_with_image(self):
        self.assertEqual(Post.objects.count(), 0)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif', content=small_gif, content_type='image/gif',
        )
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            {
                'text': 'Тестовый пост',
                'group': self.group.id,
                'image': uploaded,
            },
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:profile', args=(self.user.username,)),
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.get(id=1)
        self.assertEqual(post.text, 'Тестовый пост')
        self.assertEqual(post.group.id, self.group.id)
        self.assertEqual(post.image, 'posts/small.gif')
