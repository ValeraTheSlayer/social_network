from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModel
from core.utils import truncatechars

User = get_user_model()


class Group(models.Model):
    title = models.CharField('заголовок', max_length=200)
    slug = models.SlugField('ссылка', unique=True)
    description = models.TextField('описание')

    def __str__(self):
        return truncatechars(self.title, settings.TRUNCATE_CHARS)


class Post(CreatedModel):
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='группа',
        help_text='группа, к которой будет относиться пост',
    )
    image = models.ImageField(
        'картинка',
        upload_to='posts/',
        blank=True,
        help_text='загрузите изображение',
    )

    class Meta(CreatedModel.Meta):
        default_related_name = 'posts'
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

    def __str__(self):
        return truncatechars(self.text, settings.TRUNCATE_CHARS)


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='пост',
    )

    class Meta(CreatedModel.Meta):
        default_related_name = 'comments'

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='фоловер',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='автор блога',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_following',
            ),
        ]
