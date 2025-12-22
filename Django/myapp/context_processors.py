from django.core.cache import cache
from .models import QuestionLike, AnswerLike, Tag, Question

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
    cache_key = "sidebar_data"
    cached_data = cache.get(cache_key)
    if cached_data is None:
        popular_tags = Tag.objects.popular(8)
        popular_questions = Question.objects.hot_sidebar(5)
        cached_data = {
            'popular_tags': [
                {'id': tag.id, 'name': tag.name, 'questions_count': getattr(tag, 'questions_count', 0)}
                for tag in popular_tags
            ],
            'popular_questions': [
                {
                    'id': q.id, 
                    'title': q.title, 
                    'rating': q.rating,
                    'author_name': q.author.username
                }
                for q in popular_questions
            ]
        }
        cache.set(cache_key, cached_data, 300)

    class Object:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    return {
        'popular_tags': [Object(**tag) for tag in cached_data['popular_tags']],
        'popular_questions': [Object(**q) for q in cached_data['popular_questions']],
    }