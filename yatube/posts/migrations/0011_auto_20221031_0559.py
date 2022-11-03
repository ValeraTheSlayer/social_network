# Generated by Django 2.2.16 on 2022-10-30 23:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_auto_20221031_0522'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'default_related_name': 'comments'},
        ),
        migrations.AlterField(
            model_name='comment',
            name='text',
            field=models.TextField(
                help_text='Текст вашего комментария', verbose_name='Текст'
            ),
        ),
        migrations.AlterField(
            model_name='post',
            name='group',
            field=models.ForeignKey(
                blank=True,
                help_text='Группа, к которой будет относиться пост',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='posts',
                to='posts.Group',
                verbose_name='Группа',
            ),
        ),
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.ImageField(
                blank=True,
                help_text='Загрузите изображение',
                upload_to='posts/',
                verbose_name='Картинка',
            ),
        ),
        migrations.AlterField(
            model_name='post',
            name='text',
            field=models.TextField(
                help_text='Текст вашего поста', verbose_name='Текст'
            ),
        ),
    ]
