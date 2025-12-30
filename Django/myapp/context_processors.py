from django.core.cache import cache
from .models import QuestionLike, AnswerLike, Tag, Question
from django.core.management import call_command

def voting_context(request):
    if not request.user.is_authenticated:
        return {'user_question_votes': {}, 'user_answer_votes': {}}
    cache_key = f"user_votes_{request.user.id}"
    cached_votes = cache.get(cache_key)
    if cached_votes is None:
        user_question_votes = {
            vote.question_id: vote.type 
            for vote in QuestionLike.objects.filter(user=request.user)
        }
        print(user_question_votes)
        user_answer_votes = {
            vote.answer_id: vote.type 
            for vote in AnswerLike.objects.filter(user=request.user)
        }
        print(user_question_votes)
        cached_votes = (user_question_votes, user_answer_votes)
        cache.set(cache_key, cached_votes, 300)
        
    return {
        'user_question_votes': cached_votes[0],
        'user_answer_votes': cached_votes[1],
    }

def sidebar_context(request):
    cached_data = cache.get('sidebar_data')
    
    if cached_data is None:
        call_command('update_sidebar_cache')
        cached_data = cache.get('sidebar_data') or {
            'popular_tags': [],
            'popular_questions': [],
        }
    
    class SimpleObject:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    return {
        'popular_tags': [SimpleObject(**tag) for tag in cached_data['popular_tags']],
        'popular_questions': [SimpleObject(**q) for q in cached_data['popular_questions']],
    }