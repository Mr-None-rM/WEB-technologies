from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView, DetailView, CreateView
from django.views.decorators.http import require_POST
from .models import Question, Answer, Tag
from django.contrib.auth import login
from .forms import AskQuestionForm
from .serializers import LoginSerializer, UserRegistrationSerializer, UserSettingsSerializer
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.core.cache import cache

def paginate_objects(objects, page_number, per_page=5):
    paginator = Paginator(objects, per_page)
    try:
        return paginator.page(page_number)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)

class Settings(LoginRequiredMixin, View):
    def get(self, request):
        serializer = UserSettingsSerializer(instance=request.user)
        return render(request, 'registration/settings.html', {
            'serializer': serializer,
            'initial_data': serializer.data
        })
    
    def post(self, request):
        data = request.POST.copy()
        if 'avatar' in request.FILES:
            data['avatar'] = request.FILES['avatar']
        serializer = UserSettingsSerializer(
            instance=request.user, 
            data=data
        )
        if serializer.is_valid():
            serializer.save()
            return redirect('index')
        return render(request, 'registration/settings.html', {
            'serializer': serializer,
            'initial_data': request.POST,
            'user': request.user
        })

class RegisterView(View):
    def get(self, request):
        serializer = UserRegistrationSerializer()
        return render(request, 'registration/register.html', {
            'serializer': serializer
        })
    
    def post(self, request):
        data = request.POST.copy()
        if 'avatar' in request.FILES:
            data['avatar'] = request.FILES['avatar']
        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            print("dsfsdsdfsdfsfd")
            user = serializer.save()
            if user:
                login(request, user)
                return redirect('index')
        return render(request, 'registration/register.html', {
            'serializer': serializer,
            'initial_data': request.POST,
        })

class LoginView(View):
    def get(self, request):
        serializer = LoginSerializer()
        return render(request, 'registration/login.html', {
            'serializer': serializer
        })
    
    def post(self, request):
        serializer = LoginSerializer(data=request.POST)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            return redirect('index')
        return render(request, 'registration/login.html', {
            'serializer': serializer,
            'initial_data': request.POST
        })

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

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        return Question.objects.search(query)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        context['query'] = query
        context['page_title'] = f'Search results for "{query}"'
        return context

class QuestionDetail(DetailView):
    model = Question
    template_name = "myapp/question.html"
    context_object_name = 'question'
    pk_url_kwarg = 'question_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        answers = Answer.objects.for_question(self.object.id)
        page = self.request.GET.get('page')
        context['answers'] = paginate_objects(answers, page, per_page=5)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        answer_content = request.POST.get('answer_content')
        if answer_content and request.user.is_authenticated:
            Answer.objects.create(
                content=answer_content,
                question=self.object,
                author=request.user
            )
        return redirect('question_detail', question_id=self.object.id)

class AskQuestion(LoginRequiredMixin, CreateView):
    model = Question
    form_class = AskQuestionForm
    template_name = "myapp/ask.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('question_detail', kwargs={'question_id': self.object.id})

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
        if request.htmx:
            return HttpResponse(
                '<script>window.location.href = "{}";</script>'.format(reverse('login')),
                content_type='text/html'
            )
        return redirect('login')
    try:
        answer = Answer.objects.get(id=answer_id)
        current_status = answer.is_accepted
        if current_status:
            answer.is_accepted = False
            answer.save()
        else:
            answer.is_accepted = True
            answer.save()
        answer.refresh_from_db()
        return render(request, 'myapp/answer_item.html', {
        'answer': answer,
        'question': answer.question,
        'user': request.user,
        })
    except Answer.DoesNotExist:
        return JsonResponse({'error': 'Answer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)