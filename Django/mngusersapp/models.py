from django.db import models
from django.db.models import Index
from django.contrib.auth.models import User
from django.conf import settings
import os

def user_profile_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'profile_image.{ext}'
    return os.path.join('profiles', f'user_{instance.user.id}', filename)

class Profile(models.Model):
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        db_index=True,
        related_name='profile',
        verbose_name='Пользователь'
    )
    
    nickname = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Никнейм'
    )
    
    avatar = models.ImageField(
        upload_to=user_profile_image_path,
        verbose_name='Изображение профиля',
        blank=True,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
        indexes = [
            Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Профиль {self.nickname}'
    
    @property
    def image_url(self):
        if self.avatar:
            return self.avatar.url
        return f'{settings.MEDIA_URL}profiles/default.png'