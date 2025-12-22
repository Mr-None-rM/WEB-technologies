from django.db import models, transaction
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
            models.Index(fields=['is_answered']),
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
    
    def _update_rating(self, old_vote_type, new_vote_type):
        rating_change = 0
        if old_vote_type == VoteType.LIKE:
            rating_change -= 1
        elif old_vote_type == VoteType.DISLIKE:
            rating_change += 1
        if new_vote_type == VoteType.LIKE:
            rating_change += 1
        elif new_vote_type == VoteType.DISLIKE:
            rating_change -= 1
        self.rating += rating_change
        self.save()

    def add_user_vote(self, user, vote_type):
        if user == self.author:
            raise ValueError("Нельзя голосовать за свой вопрос")
        if vote_type not in VoteType.values:
            raise ValueError("Некорректный тип голоса")
        with transaction.atomic():
            question = Question.objects.select_for_update().get(pk=self.pk)
            previous_vote = question.ratings.filter(user=user).first()
            old_type = previous_vote.type if previous_vote else None
            if previous_vote:
                previous_vote.delete()
            QuestionLike.objects.create(
                question=question,
                user=user,
                type=vote_type
            )
            question._update_rating(old_type, vote_type)

    def remove_vote(self, user):
        with transaction.atomic():
            question = Question.objects.select_for_update().get(pk=self.pk)
            previous_vote = question.ratings.filter(user=user).first()
            if previous_vote:
                question._update_rating(previous_vote.type, None)
                previous_vote.delete()

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
    
    def _update_rating(self, old_vote_type, new_vote_type):
        rating_change = 0
        if old_vote_type == VoteType.LIKE:
            rating_change -= 1
        elif old_vote_type == VoteType.DISLIKE:
            rating_change += 1
        if new_vote_type == VoteType.LIKE:
            rating_change += 1
        elif new_vote_type == VoteType.DISLIKE:
            rating_change -= 1
        self.rating += rating_change
        self.save()

    def add_user_vote(self, user, vote_type):
        if user == self.author:
            raise ValueError("Нельзя голосовать за свой вопрос")
        if vote_type not in VoteType.values:
            raise ValueError("Некорректный тип голоса")
        with transaction.atomic():
            answer = Answer.objects.select_for_update().get(pk=self.pk)
            previous_vote = answer.ratings.filter(user=user).first()
            old_type = previous_vote.type if previous_vote else None
            if previous_vote:
                previous_vote.delete()
            AnswerLike.objects.create(
                answer=answer,
                user=user,
                type=vote_type
            )
            answer._update_rating(old_type, vote_type)

    def remove_vote(self, user):
        with transaction.atomic():
            answer = Answer.objects.select_for_update().get(pk=self.pk)
            previous_vote = answer.ratings.filter(user=user).first()
            if previous_vote:
                answer._update_rating(previous_vote.type, None)
                previous_vote.delete()

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