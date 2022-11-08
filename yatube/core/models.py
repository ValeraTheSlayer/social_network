from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class CreatedModel(models.Model):
    pub_date = models.DateTimeField(
        'дата создания',
        auto_now_add=True,
        db_index=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='автор',
    )
    text = models.TextField(
        'текст',
        help_text='ваш текст',
    )

    class Meta:
        abstract = True
        ordering = ('-pub_date',)
