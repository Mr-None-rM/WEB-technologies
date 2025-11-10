from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
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

class Index(View):
    def get(self, request):
        questions = Question.objects.new()
        page = request.GET.get('page')
        paginated_questions = paginate_objects(questions, page, per_page=5)
        return render(request, "myapp/index.html", {
            'questions': paginated_questions
        })
    
class HotQuestions(View):
    def get(self, request):
        questions = Question.objects.hot()
        page = request.GET.get('page')
        paginated_questions = paginate_objects(questions, page, per_page=5)
        return render(request, "myapp/index.html", {
            'questions': paginated_questions
        })
    
class Search(View):
    def get(self, request):
        query = request.GET.get('q', '').strip()
        questions = Question.objects.search(query)
        page_title = f'Search results for "{query}"'
        page = request.GET.get('page')
        paginated_questions = paginate_objects(questions, page, per_page=5)
        return render(request, "myapp/search.html", {
            'questions': paginated_questions,
            'query': query,
            'page_title': page_title
        })

class QuestionDetail(LoginRequiredMixin, View):
    def get(self, request, question_id):
        question = get_object_or_404(Question, id=question_id)
        answers = Answer.objects.for_question(question_id)
        page = request.GET.get('page')
        paginated_answers = paginate_objects(answers, page, per_page=5)
        return render(request, "myapp/question.html", {
            'question': question,
            'answers': paginated_answers
        })
    
    def post(self, request, question_id):
        question = get_object_or_404(Question, id=question_id)
        answer_content = request.POST.get('answer_content')
        if answer_content:
            Answer.objects.create(
                content=answer_content,
                question=question,
                author=request.user
            )
        return redirect('question_detail', question_id=question_id)

class AskQuestion(LoginRequiredMixin, View):
    def get(self, request):
        form = AskQuestionForm()
        return render(request, "myapp/ask.html", {
            'form': form
        })
    
    def post(self, request):
        form = AskQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(request.user)
            return redirect('question_detail', question_id=question.id)
        return render(request, "myapp/ask.html", {
            'form': form
        })

class TagQuestions(LoginRequiredMixin, View):
    def get(self, request, tag_id):
        tag = get_object_or_404(Tag, id=tag_id)
        questions = Question.objects.with_tag(tag.name)
        page = request.GET.get('page')
        paginated_questions = paginate_objects(questions, page, per_page=5)
        return render(request, "myapp/tag.html", {
            'tag': tag,
            'questions': paginated_questions,
        })
    
#HTMX для оценки вопросов и ответов и принятия ответов автором
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