from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from mixer.backend.django import mixer

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = mixer.blend('posts.Post')

    def test_models_have_correct_object_names(self):
        self.assertEqual(
            self.post.text[: settings.TRANCATE_CHARS] + '…',
            str(self.post),
        )


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = mixer.blend('posts.Group')

    def test_models_have_correct_object_names(self):
        self.assertEqual(
            self.group.title[: settings.TRANCATE_CHARS] + '…',
            str(self.group),
        )
