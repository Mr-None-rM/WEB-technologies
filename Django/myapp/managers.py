from django.db import models
from django.db.models import Count, Q
from django.core.exceptions import ObjectDoesNotExist

class QuestionManager(models.Manager):
    def new(self):
        return self.get_queryset().order_by('-created_at')
    
    def with_tag(self, tag_name):
        return self.get_queryset().filter(
            tags__name=tag_name
        ).order_by('-created_at')
    
    def hot(self):
        return self.get_queryset().order_by('-rating', '-created_at')
    
    def hot_sidebar(self, limit=5):
        return self.get_queryset().select_related('author').only(
            'id', 'title', 'rating', 'author__id', 'author__username'
        ).order_by('-rating')[:limit]
    
    def search(self, query):
        return self.get_queryset().filter(
            models.Q(title__icontains=query) |
            models.Q(tags__name__icontains=query) |
            models.Q(content__icontains=query)
        ).distinct().order_by('-created_at')

class AnswerManager(models.Manager):
    def for_question(self, question_id):
        return self.get_queryset().filter(
            question_id=question_id
        ).order_by('-is_accepted', '-rating', '-created_at')

class TagManager(models.Manager):
    def popular(self, limit=10):
        return self.get_queryset().annotate(
            questions_count=Count('questions')
        ).order_by('-questions_count')[:limit]
    
class ProfileManager(models.Manager):
    def get_user_profile(self, user):
        try:
            return user.profile
        except ObjectDoesNotExist:
            return self.create(user=user)
    
    def update_user_profile(self, user, **kwargs):
        profile = self.get_user_profile(user)
        for key, value in kwargs.items():
            setattr(profile, key, value)
        profile.save()
        return profile