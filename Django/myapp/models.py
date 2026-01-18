from django.db import models, transaction
from django.db.models import Count, Case, When, Value, IntegerField
from django.contrib.auth.models import User
from django.urls import reverse
from .managers import QuestionManager, AnswerManager, TagManager
from django.core.exceptions import PermissionDenied

def user_profile_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'profile_image.{ext}'
    return os.path.join('profiles', f'user_{instance.user.id}', filename)
    
class Tag(models.Model):

    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Название тега'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    objects = TagManager()
    
    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'])
        ]
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('tag_questions', kwargs={'tag_id': self.id})
    
class Question(models.Model):

    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок вопроса'
    )
    
    content = models.TextField(
        max_length=1000,
        verbose_name='Содержание вопроса'
    )
    
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Автор вопроса'
    )
    
    tags = models.ManyToManyField(
        Tag,
        related_name='questions',
        blank=True,
        verbose_name='Теги'
    )

    rating = models.IntegerField(
        default=0, 
        verbose_name='Рейтинг'
    )
    
    is_answered = models.BooleanField(
        default=False,
        verbose_name='Есть принятый ответ'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    objects = QuestionManager()
    
    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['rating']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['title']),
            models.Index(fields=['content'])
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('question_detail', kwargs={'question_id': self.id})
    
    def get_user_vote(self, user):
        if user.is_authenticated:
            try:
                vote = self.ratings.get(user=user)
                return vote.type
            except QuestionLike.DoesNotExist:
                return None
        return None
    
    def _update_rating(self):
        likes_aggregate = self.ratings.aggregate(
            rating_diff=Count(
                Case(
                    When(type=VoteType.LIKE, then=Value(1)),
                    When(type=VoteType.DISLIKE, then=Value(-1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )
        )
        self.rating = likes_aggregate['rating_diff'] or 0
        self.save(update_fields=['rating'])

    def add_user_vote(self, user, vote_type):
        if user == self.author:
            raise ValueError("Нельзя голосовать за свой вопрос")
        if vote_type not in VoteType.values:
            raise ValueError("Некорректный тип голоса")
        with transaction.atomic():
            previous_vote = self.ratings.filter(user=user).first()
            if previous_vote:
                if previous_vote.type == vote_type:
                    previous_vote.delete()
                else:
                    previous_vote.type = vote_type
                    previous_vote.save()
            else:
                QuestionLike.objects.create(
                    question=self,
                    user=user,
                    type=vote_type
                )
            self._update_rating()

    def remove_vote(self, user):
        with transaction.atomic():
            previous_vote = self.ratings.filter(user=user).first()
            if previous_vote:
                previous_vote.delete()
                self._update_rating()

class Answer(models.Model):

    content = models.TextField(
        verbose_name='Содержание ответа'
    )
    
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Вопрос'
    )
    
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Автор ответа'
    )

    rating = models.IntegerField(
        default=0, 
        verbose_name='Рейтинг'
    )
    
    is_accepted = models.BooleanField(
        default=False,
        verbose_name='Принятый ответ'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    objects = AnswerManager()
    
    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'
        ordering = ['-is_accepted', 'created_at']
        indexes = [
            models.Index(fields=['question', 'is_accepted']),
            models.Index(fields=['created_at']),
            models.Index(fields=['rating']),
            models.Index(fields=['author', 'created_at']),
        ]
    
    def __str__(self):
        return f"Ответ на '{self.question.title}'"
    
    def get_user_vote(self, user):
        if user.is_authenticated:
            try:
                vote = self.ratings.get(user=user)
                return vote.type
            except AnswerLike.DoesNotExist:
                return None
        return None
    
    def _update_rating(self):
        likes_aggregate = self.ratings.aggregate(
            rating_diff=Count(
                Case(
                    When(type=VoteType.LIKE, then=Value(1)),
                    When(type=VoteType.DISLIKE, then=Value(-1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )
        )
        self.rating = likes_aggregate['rating_diff'] or 0
        self.save(update_fields=['rating'])

    def add_user_vote(self, user, vote_type):
        if user == self.author:
            raise ValueError("Нельзя голосовать за свой вопрос")
        if vote_type not in VoteType.values:
            raise ValueError("Некорректный тип голоса")
        with transaction.atomic():
            previous_vote = self.ratings.filter(user=user).first()
            if previous_vote:
                if previous_vote.type == vote_type:
                    previous_vote.delete()
                else:
                    previous_vote.type = vote_type
                    previous_vote.save()
            else:
                AnswerLike.objects.create(
                    answer=self,
                    user=user,
                    type=vote_type
                )
            self._update_rating()

    def remove_vote(self, user):
        with transaction.atomic():
            previous_vote = self.ratings.filter(user=user).first()
            if previous_vote:
                previous_vote.delete()
                self._update_rating()

    def toggle_accept(self, user):
        if user != self.question.author:
            raise PermissionDenied("Только автор вопроса может отмечать ответы как правильные")
        if self.is_accepted:
            self.is_accepted = False
            self.save()
            return False
        with transaction.atomic():
            Answer.objects.filter(question=self.question).update(is_accepted=False)
            self.is_accepted = True
            self.save()
        return True

class VoteType(models.TextChoices):
        LIKE = 'like', 'Like'
        DISLIKE = 'dislike', 'Dislike'

class QuestionLike(models.Model):
    
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name='Вопрос'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )

    type = models.CharField(
        max_length=10,
        choices=VoteType.choices,
        default=VoteType.LIKE,
        verbose_name='Тип голоса'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Лайк вопроса'
        verbose_name_plural = 'Лайки вопросов'
        unique_together = ['question', 'user']
        indexes = [
            models.Index(fields=['question', 'user']),
            models.Index(fields=['type']),
        ]
    
    def __str__(self):
        return f"Лайк {self.user.username} на вопрос '{self.question.title}'"
    
    def save(self, *args, **kwargs):
        if self.question.author == self.user:
            raise ValueError("Нельзя лайкать свой вопрос")
        super().save(*args, **kwargs)

class AnswerLike(models.Model):

    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name='Ответ'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='answer_likes',
        verbose_name='Пользователь'
    )

    type = models.CharField(
        max_length=10,
        choices=VoteType.choices,
        default=VoteType.LIKE,
        verbose_name='Тип голоса'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Лайк ответа'
        verbose_name_plural = 'Лайки ответов'
        unique_together = ['answer', 'user']
        indexes = [
            models.Index(fields=['answer', 'user']),
            models.Index(fields=['type']),
        ]
    
    def __str__(self):
        return f"Лайк {self.user.username} на ответ к '{self.answer.question.title}'"
    
    def save(self, *args, **kwargs):
        if self.answer.author == self.user:
            raise ValueError("Нельзя лайкать свой ответ")
        super().save(*args, **kwargs)