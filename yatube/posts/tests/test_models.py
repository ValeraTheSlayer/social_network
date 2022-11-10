from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from mixer.backend.django import mixer

from core.utils import truncatechars

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = mixer.blend('posts.Post')

    def test_model_have_correct_object_names(self):
        self.assertEqual(
            truncatechars(self.post.text, settings.TRUNCATE_CHARS),
            str(self.post),
        )


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = mixer.blend('posts.Group')

    def test_model_have_correct_object_names(self):
        self.assertEqual(
            truncatechars(self.group.title, settings.TRUNCATE_CHARS),
            str(self.group),
        )
