import json
import time
import jwt
import requests
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, FormView, TemplateView
from django.views.decorators.http import require_POST, require_GET
from .models import Question, Answer, Tag
from .forms import AskQuestionForm, AnswerForm
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.core.cache import cache
from cent import Client, PublishRequest

def generate_token(user_id):
    token = jwt.encode({
        "sub": str(user_id),
        "exp": int(time.time() * 10 * 60),
    }, settings.CENTRIFUGO_HMAC_SECRET, algorithm="HS256")
    return token

def publish_to_centrifuge(channel, data):
    api_url = f"http://centrifugo:8010/api"
    client = Client(api_url, settings.CENTRIFUGO_API_KEY)
    request = PublishRequest(channel=channel, data=data)
    client.publish(request)

def paginate_objects(objects, page_number, per_page=5):
    paginator = Paginator(objects, per_page)
    try:
        return paginator.page(page_number)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)

class Index(ListView):
    model = Question
    template_name = "myapp/index.html"
    context_object_name = 'questions'
    paginate_by = 5

    def get_queryset(self):
        return Question.objects.new()

class HotQuestions(ListView):
    model = Question
    template_name = "myapp/index.html"
    context_object_name = 'questions'
    paginate_by = 5

    def get_queryset(self):
        return Question.objects.hot()

class Search(ListView):
    model = Question
    template_name = "myapp/search.html"
    context_object_name = 'questions'
    paginate_by = 5
    
    def dispatch(self, request, *args, **kwargs):
        self.query = request.GET.get('q', '').strip()
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        if not self.query:
            return Question.objects.none()
        return Question.objects.search(self.query)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.query
        return context
    
class SearchPopupView(TemplateView):
    template_name = "myapp/search_popup.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        context['query'] = query
        if query:
            questions = Question.objects.search(query)[:5]
            context['questions'] = questions
            context['show_more'] = Question.objects.search(query).count() > 5
        else:
            context['questions'] = Question.objects.none()
            context['show_more'] = False
            
        return context

class QuestionDetail(DetailView):
    #Тут тоже позже понадобится поправить логику запросов к БД, тут 2 запроса с повторной логикой 
    model = Question
    template_name = "myapp/question.html"
    context_object_name = 'question'
    pk_url_kwarg = 'question_id'

    def get_object(self, queryset=None):
        return Question.objects.for_detail(self.kwargs['question_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        answers = Answer.objects.for_question(self.object.id)
        page = self.request.GET.get('page')
        context['answers'] = paginate_objects(answers, page, per_page=5)
        if self.request.user.is_authenticated:
            context['centrifuge_token'] = generate_token(self.request.user.pk)
            context['centrifuge_user_id'] = str(self.request.user.pk)
        else:
            context['centrifuge_token'] = generate_token("UNAUTH")
            context['centrifuge_user_id'] = "UNAUTH"
        context['centrifuge_url'] = settings.CENTRIFUGO_URL
        context['centrifuge_channel'] = f"question_{self.object.id}"
        return context

class AskQuestion(LoginRequiredMixin, FormView):
    form_class = AskQuestionForm
    template_name = "myapp/ask.html"
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['author'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        self.question = form.save()
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('question_detail', kwargs={'question_id': self.question.id})
    
class CreateAnswerView(LoginRequiredMixin, FormView):
    form_class = AnswerForm
    template_name = "myapp/create_answer.html"
    
    def dispatch(self, request, *args, **kwargs):
        self.question = Question.objects.for_detail(kwargs['question_id'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['author'] = self.request.user
        kwargs['question'] = self.question
        return kwargs
    
    def form_valid(self, form):
        answer = form.save()
        profile_image_url = '/media/profiles/default.png'
        if hasattr(self.request.user, 'profile') and self.request.user.profile.image_url:
            profile_image_url = self.request.user.profile.image_url
        answer_data = {
            'type': 'new_answer',
            'answer_id': answer.id,
            'content': answer.content[:500],
            'author_id': self.request.user.id,
            'author_username': self.request.user.username,
            'profile_image_url': profile_image_url,
            'created_at': answer.created_at.isoformat(),
            'question_id': self.question.id
        }
        
        channel = f"question_{self.question.id}"
        publish_to_centrifuge(channel, answer_data)
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['question'] = self.question
        return context
    
    def get_success_url(self):
        return reverse('question_detail', kwargs={'question_id': self.question.id})

class TagQuestions(LoginRequiredMixin, ListView):
    model = Question
    template_name = "myapp/tag.html"
    context_object_name = 'questions'
    paginate_by = 5

    def get_queryset(self):
        tag = get_object_or_404(Tag, id=self.kwargs['tag_id'])
        return Question.objects.with_tag(tag.name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = get_object_or_404(Tag, id=self.kwargs['tag_id'])
        return context

@require_POST
def vote_question(request, question_id):
    if not request.user.is_authenticated:
        if request.htmx:
            return HttpResponse(
                '<script>window.location.href = "{}";</script>'.format(reverse('login')),
                content_type='text/html'
            )
        return redirect('login')
    try:
        question = Question.objects.get(id=question_id)
        type = request.POST.get('type')
        current_vote = question.get_user_vote(request.user)
        if current_vote == type:
            question.remove_vote(request.user)
            new_vote = None
        else:
            question.add_user_vote(request.user, type)
            new_vote = type
        question.refresh_from_db()
        cache.delete(f"user_votes_{request.user.id}")
        return render(request, 'myapp/voting_question.html', {
            'question': question,
            'current_vote': new_vote
        })
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Question not found'}, status=404)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_POST
def vote_answer(request, answer_id):
    if not request.user.is_authenticated:
        if request.htmx:
            return HttpResponse(
                '<script>window.location.href = "{}";</script>'.format(reverse('login')),
                content_type='text/html'
            )
        return redirect('login')
    try:
        answer = Answer.objects.get(id=answer_id)
        type = request.POST.get('type')
        current_vote = answer.get_user_vote(request.user)
        if current_vote == type:
            answer.remove_vote(request.user)
            new_vote = None
        else:
            answer.add_user_vote(request.user, type)
            new_vote = type
        answer.refresh_from_db()
        cache.delete(f"user_votes_{request.user.id}")
        return render(request, 'myapp/voting_answer.html', {
            'answer': answer,
            'current_vote': new_vote
        })
    except Answer.DoesNotExist:
        return JsonResponse({'error': 'Answer not found'}, status=404)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

@require_POST
def toggle_accept_answer(request, answer_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=403)
    try:
        answer = Answer.objects.get(id=answer_id)
        answer.is_accepted = not answer.is_accepted
        answer.save()
        if request.htmx:
            return render(request, 'myapp/answer_item.html', {
                'answer': answer,
                'question': answer.question,
                'user': request.user,
            })
        return JsonResponse({'is_accepted': answer.is_accepted})
    except Answer.DoesNotExist:
        return JsonResponse({'error': 'Answer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)