from django.core.management.base import BaseCommand
from django.core.cache import cache
from myapp.models import Tag, Question, User

class Command(BaseCommand):
    help = 'Update sidebar cache'
    
    def handle(self, *args, **options):
        popular_tags = Tag.objects.popular(10)
        popular_questions = Question.objects.hot_sidebar(10)
        sidebar_data = {
            'popular_tags': [
                {
                    'id': tag.id,
                    'name': tag.name,
                    'questions_count': tag.questions_count,
                }
                for tag in popular_tags
            ],
            'popular_questions': [
                {
                    'id': q.id,
                    'title': q.title,
                    'rating': q.rating,
                    'author_name': q.author.username,
                }
                for q in popular_questions
            ],
        }
        
        cache.set('sidebar_data', sidebar_data, 3600)