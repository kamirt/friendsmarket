from django.conf import settings
from django.db import models
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import ugettext_lazy as _

from functools import partial
from fm.helpers import get_upload_path, save_resized_image


class UserManager(BaseUserManager):
    """
    A custom user manager to deal with emails as unique identifiers for auth
    instead of usernames. The default that's used is "UserManager"
    """
    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    SEX_TYPES = (('F', 'Женский'), ('M', 'Мужской'), ('U', 'Неопределено'))

    username = models.CharField('Имя пользователя', max_length=100, blank=True)
    first_name = models.CharField('Имя', max_length=100, blank=True)
    last_name = models.CharField('Фамилия', max_length=100, blank=True)
    email = models.EmailField('Email', unique=True)
    phone = models.CharField('Телефон', max_length=100, blank=True)
    birthday = models.DateField('Дата рождения', null=True, blank=True)
    gender = models.CharField('Пол', max_length=1, choices=SEX_TYPES, default='U')
    created = models.DateTimeField('Создан', auto_now_add=True)
    profile_photo = models.ImageField('Фото',
        upload_to=partial(get_upload_path, path='profile_photos'),
        default='profile_photos/default.png')
    enable_notif = models.BooleanField('Уведомления', default=True)
    android_regid = models.TextField(blank=True,
        verbose_name=_("Registration ID"),
        help_text=_('Android FireBase registration_id'))

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    USERNAME_FIELD = 'email'
    objects = UserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        if self.first_name and self.last_name:
            return self.first_name + ' ' + self.last_name
        elif self.first_name:
            return self.first_name
        else:
            return self.email

    def get_short_name(self):
        return self.email

    def save(self, *args, **kwargs):
        if not kwargs or ('update_fields' in kwargs) and ('profile_photo' in kwargs['update_fields']):
            self.profile_photo = save_resized_image(self.profile_photo, 400, 1)
        super(User, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('email',)

class Friend(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
        related_name='my_friends', on_delete=models.CASCADE)
    friend = models.ForeignKey(settings.AUTH_USER_MODEL,
        related_name='friend_to', on_delete=models.CASCADE)
    follow = models.BooleanField(default=False)


class Post(models.Model):
    QUESTION = 0
    POSITIVE = 1
    NEGATIVE = 2
    POST_TYPES = (
        (QUESTION, 'Вопрос'),
        (POSITIVE, 'Позитивная'),
        (NEGATIVE, 'Негативная'),
    )

    author = models.ForeignKey(settings.AUTH_USER_MODEL,
        related_name='my_posts', on_delete=models.CASCADE,
        verbose_name='Автор')
    created = models.DateTimeField(auto_now_add=True,
        verbose_name='Создан')
    typeContent = models.IntegerField(choices=POST_TYPES, default=QUESTION, db_column='type',
        verbose_name='Тип', help_text=_('Вопрос, положительная рекомендация или отрицательная'))
    title = models.CharField(max_length=100,
        verbose_name='Название')
    description = models.TextField(blank=True,
        verbose_name='Описание', help_text=_('Текст поста'))
    image = models.ImageField(
        upload_to=partial(get_upload_path, path='posts_images'), blank=True, null=True,
        verbose_name='Изображение')
    tags = models.ManyToManyField('Tag',
        verbose_name='Теги')
    city = models.ForeignKey('city', related_name='post_city', null=True, on_delete=models.SET_NULL,
        verbose_name='Город')
    best_note = models.ForeignKey('self',
        related_name='+', null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name='Лучшая рекомендация', help_text=_('Лучшая рекомендация к данному вопросу'))
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
        related_name='post_likes', verbose_name='Понравилось')
    follows = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
        related_name='post_follows', verbose_name='Отслеживают')
    viewed = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
        related_name='posts_viewed', verbose_name=_('Прочитали'))

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not kwargs or ('update_fields' in kwargs) and ('image' in kwargs['update_fields']):
            if self.image:
                self.image = save_resized_image(self.image, 800, 16/9)
        super(Post, self).save(*args, **kwargs)


    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ('-created',)

class Tag(models.Model):
    tag = models.CharField(max_length=100, blank=False, unique=True,
        verbose_name='Тег')

    def __str__(self):
        return self.tag

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('tag',)

class Comment(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
        related_name='user_comments', on_delete=models.CASCADE,
        verbose_name='Автор')
    post = models.ForeignKey('Post',
        related_name='post_comments', on_delete=models.CASCADE,
        verbose_name='Пост')
    created = models.DateTimeField(auto_now_add=True,
        verbose_name='Создан')
    comment = models.TextField(null=True, blank=True,
        verbose_name='Комментарий')
    note = models.ForeignKey('Post', null=True, blank=True,
        related_name='note', on_delete=models.CASCADE,
        verbose_name='Прикреплен')
    parent = models.ForeignKey('self', null=True, blank=True,
        related_name='comment_reply', on_delete=models.SET_NULL,
        verbose_name='Родитель')
    reply_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Ответ')

    def __str__(self):
        return self.comment

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('created',)

class City(models.Model):
    name = models.CharField(max_length=100, blank=False, unique=True,
        verbose_name='Город')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'
        ordering = ('name', )
