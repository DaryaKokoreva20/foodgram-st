from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from constants import (
    FIRST_NAME_MAX_LENGTH,
    LAST_NAME_MAX_LENGTH
)


class User(AbstractUser):
    """Кастомная модель пользователя с уникальным идентификатором email."""

    email = models.EmailField(
        unique=True,
        verbose_name='Электронная почта'
    )
    first_name = models.CharField(
        max_length=FIRST_NAME_MAX_LENGTH,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=LAST_NAME_MAX_LENGTH,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Аватар'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Модель подписки пользователя на авторов рецептов."""

    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_follow'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def clean(self):
        """Запрещает пользователю подписываться на самого себя."""
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на самого себя.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} follows {self.author}'
