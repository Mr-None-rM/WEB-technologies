from django.db import models
from django.db.models import Count

class QuestionManager(models.Manager):
    def new(self):
        return self.get_queryset().select_related(
            'author', 
            'author__profile'
        ).prefetch_related(
            'tags'
        ).annotate(
            answers_count=Count('answers')
        ).order_by('-created_at')
    
    def with_tag(self, tag_name):
        return self.get_queryset().select_related(
            'author',
            'author__profile'
        ).prefetch_related(
            'tags'
        ).annotate(
            answers_count=Count('answers')
        ).filter(
            tags__name=tag_name
        ).order_by('-created_at')
    
    def hot(self):
        return self.get_queryset().select_related(
            'author',
            'author__profile'
        ).prefetch_related(
            'tags'
        ).annotate(
            answers_count=Count('answers')
        ).order_by('-rating', '-created_at')
    
    def hot_sidebar(self, limit=5):
        return self.get_queryset().select_related(
            'author',
            'author__profile'
        ).only(
            'id', 'title', 'rating', 'author__id', 'author__username',
            'author__profile__nickname', 'author__profile__avatar'
        ).annotate(
            answers_count=Count('answers')
        ).order_by('-rating')[:limit]
    
    def search(self, query):
        return self.get_queryset().select_related(
            'author',
            'author__profile'
        ).prefetch_related(
            'tags'
        ).annotate(
            answers_count=Count('answers')
        ).filter(
            models.Q(title__icontains=query) |
            models.Q(tags__name__icontains=query) |
            models.Q(content__icontains=query)
        ).distinct().order_by('-created_at')
    
    def for_detail(self, question_id):
        return (self.get_queryset().select_related(
            'author', 
            'author__profile'
        ).prefetch_related(
            'tags'
        ).annotate(
            answers_count=Count('answers')
        ).get(id=question_id))

class AnswerManager(models.Manager):
    def for_question(self, question_id):
        return self.get_queryset().select_related(
            'author',
            'author__profile'
        ).filter(
            question_id=question_id
        ).order_by('-is_accepted', '-rating', '-created_at')

class TagManager(models.Manager):
    def popular(self, limit=10):
        return self.get_queryset().annotate(
            questions_count=Count('questions')
        ).order_by('-questions_count')[:limit]
