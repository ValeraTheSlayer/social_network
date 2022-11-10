import shutil

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from mixer.backend.django import mixer

from posts.models import Follow, Post
from posts.tests import consts
from posts.tests.common import image

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.anon = Client()
        cls.auth = Client()
        cls.auth.force_login(cls.user)
        cls.follower = User.objects.create_user(username='follower')
        cls.auth_follower = Client()
        cls.auth_follower.force_login(cls.follower)
        cls.group = mixer.blend('posts.Group')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.urls = (
            (
                'posts:index',
                'posts/index.html',
                None,
            ),
            (
                'posts:group_list',
                'posts/group_list.html',
                (cls.group.slug,),
            ),
            (
                'posts:profile',
                'posts/profile.html',
                (cls.user.username,),
            ),
            (
                'posts:post_detail',
                'posts/post_detail.html',
                (cls.post.id,),
            ),
            (
                'posts:post_create',
                'posts/create_post.html',
                None,
            ),
            (
                'posts:post_edit',
                'posts/create_post.html',
                (cls.post.id,),
            ),
            ('posts:follow_index', 'posts/follow.html', None),
        )

    def setUp(self):
        cache.clear()

    def test_pages_uses_correct_template(self):
        for reverse_name, template, params in self.urls:
            with self.subTest(
                reverse_name=reverse_name,
                template=template,
                params=params,
            ):
                response = self.auth.get(
                    reverse(reverse_name, args=params),
                )
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        response = self.anon.get(reverse('posts:index'))
        expected = Post.objects.all()[:settings.PAGE_SIZE]
        self.assertEqual(
            response.context['page_obj'][:settings.PAGE_SIZE],
            list(expected),
        )

    def test_group_list_correct_context(self):
        response = self.anon.get(
            reverse('posts:group_list', args=(self.group.slug,)),
        )
        expected = Post.objects.filter(group_id=self.group.id)[
            :settings.PAGE_SIZE
        ]
        self.assertEqual(
            response.context['page_obj'][:settings.PAGE_SIZE],
            list(expected),
        )

    def test_profile_correct_context(self):
        response = self.anon.get(
            reverse(
                'posts:profile',
                args=(self.user.username,),
            ),
        )
        expected = Post.objects.filter(author_id=self.user.id)[
            :settings.PAGE_SIZE
        ]
        self.assertEqual(
            response.context['page_obj'][:settings.PAGE_SIZE],
            list(expected),
        )

    def test_post_detail_correct_context(self):
        response = self.anon.get(
            reverse(
                'posts:post_detail',
                args=(self.post.id,),
            ),
        )
        self.assertEqual(
            response.context.get('post').author,
            self.user,
        )
        self.assertEqual(response.context.get('post').text, 'Тестовый пост')
        self.assertEqual(
            response.context.get('post').group,
            self.group,
        )

    def test_post_create_correct_context(self):
        response = self.auth.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_edit_correct_context(self):
        response = self.auth.get(
            reverse(
                'posts:post_edit',
                args=(self.post.id,),
            ),
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_check_group_in_pages(self):
        form_fields = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                args=(self.group.slug,),
            ),
            reverse(
                'posts:profile',
                args=(self.user.username,),
            ),
        )
        for value in form_fields:
            with self.subTest(value=value):
                response = self.auth.get(value)
                form_field = response.context['page_obj']
                self.assertIn(
                    Post.objects.get(group=self.post.group), form_field
                )

    def test_check_group_not_in_mistake_group_list_page(self):
        form_fields = {
            reverse(
                'posts:group_list',
                args=(self.group.slug,),
            ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.auth.get(value)
                form_field = response.context['page_obj']
                self.assertNotIn(expected, form_field)

    def test_new_post_of_following_author_appears_in_follower_list(self):
        Follow.objects.create(user=self.follower, author=self.user)
        response_1 = self.auth_follower.get(reverse('posts:index'))
        post = response_1.context['page_obj'][0]
        response_2 = self.auth_follower.get(reverse('posts:follow_index'))
        self.assertIn(post, response_2.context['page_obj'])

    def test_new_post_of_unfollowing_author_not_appears_in_follower_list(self):
        response_1 = self.auth_follower.get(reverse('posts:index'))
        post = response_1.context['page_obj'][0]
        response_2 = self.auth_follower.get(reverse('posts:follow_index'))
        self.assertNotIn(post, response_2.context['page_obj'])

    def test_authorized_user_can_follow_other_users(self):
        Follow.objects.create(user=self.follower, author=self.user)
        self.assertTrue(self.user.following.exists())

    def test_authorized_user_can_unfollow_other_users(self):
        Follow.objects.create(user=self.follower, author=self.user)
        self.assertTrue(self.user.following.exists())
        Follow.objects.get(user=self.follower, author=self.user).delete()
        self.assertFalse(self.user.following.exists())


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.anon = Client()
        cls.group = mixer.blend('posts.Group')
        for post_number in range(consts.POSTS_AMOUNT):
            cls.post = Post.objects.create(
                author=cls.user,
                text='Тестовый пост' + str(post_number),
                group=cls.group,
            )

    def setUp(self):
        cache.clear()

    def test_first_page_contains_ten_records(self):
        posts_per_page = {
            reverse('posts:index'): settings.PAGE_SIZE,
            reverse(
                'posts:group_list',
                args=(self.group.slug,),
            ): settings.PAGE_SIZE,
            reverse(
                'posts:profile',
                args=(self.user.username,),
            ): settings.PAGE_SIZE,
        }
        for reverse_name, paginator_posts in posts_per_page.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.anon.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']),
                    paginator_posts,
                )

    def test_second_page_contains_three_records(self):
        posts_per_page = {
            reverse('posts:index') + '?page=2': consts.PAGINATOR_SECOND_PAGE,
            reverse('posts:group_list', args=(self.group.slug,))
            + '?page=2': consts.PAGINATOR_SECOND_PAGE,
            reverse(
                'posts:profile',
                args=(self.user.username,),
            )
            + '?page=2': consts.PAGINATOR_SECOND_PAGE,
        }
        for reverse_name, paginator_posts in posts_per_page.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.anon.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']),
                    paginator_posts,
                )
                cache.clear()


@override_settings(MEDIA_ROOT=settings.MEDIA_ROOT)
class PostUploadImageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.anon = Client()
        cls.auth = Client()
        cls.auth.force_login(cls.user)
        cls.group = mixer.blend('posts.Group')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=image(),
        )
        cls.image_urls = (
            (reverse('posts:index')),
            (reverse('posts:group_list', args=(cls.group.slug,))),
            (reverse('posts:profile', args=(cls.user.username,))),
        )

    def setUp(self):
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def test_show_image_in_context_pages(self):
        for url in self.image_urls:
            with self.subTest(url):
                response = self.anon.get(url)
                self.assertEqual(
                    response.context['page_obj'][0].image, self.post.image
                )

    def test_show_image_in_context_post_detail(self):
        response = self.anon.get(
            reverse(
                'posts:post_detail',
                args=(self.post.id,),
            ),
        )
        self.assertEqual(response.context['post'].image, self.post.image)

    def test_check_cache(self):
        response = self.anon.get(reverse('posts:index'))
        Post.objects.get(id=1).delete()
        response2 = self.anon.get(reverse('posts:index'))
        self.assertEqual(response.content, response2.content)
        cache.clear()
        response3 = self.anon.get(reverse('posts:index'))
        self.assertNotEqual(response.content, response3.content)
