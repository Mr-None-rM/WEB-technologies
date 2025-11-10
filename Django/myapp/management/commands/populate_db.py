import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import Question, Answer, Tag, QuestionLike, AnswerLike, Profile
from faker import Faker
from tqdm import tqdm

class Command(BaseCommand):
    help = 'Fill database with test data'
    
    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int, help='Fill ratio coefficient')
    
    def handle(self, *args, **options):
        ratio = options['ratio']
        fake = Faker()
        num_users = ratio
        num_questions = ratio * 10
        num_answers = ratio * 100
        num_tags = ratio
        num_question_likes = ratio * 100
        num_answer_likes = ratio * 100

        users = []
        for _ in tqdm(range(num_users)):
            username = fake.unique.user_name()
            email = fake.unique.email()
            user = User(username=username, email=email)
            users.append(user)
        User.objects.bulk_create(users, batch_size=1000)
        users = list(User.objects.all())

        profiles = []
        for user in tqdm(users):
            profile = Profile(
                user=user,
                nickname=user.username
            )
            profiles.append(profile)
        Profile.objects.bulk_create(profiles, batch_size=1000)

        tags = []
        for _ in tqdm(range(num_tags)):
            name = fake.unique.word()
            tag = Tag(name=name)
            tags.append(tag)
        Tag.objects.bulk_create(tags, batch_size=1000)
        tags = list(Tag.objects.all())

        questions = []
        for _ in tqdm(range(num_questions)):
            title = fake.sentence()[:200]
            content = fake.text(max_nb_chars=1000)
            author = random.choice(users)
            question = Question(title=title, content=content, author=author)
            questions.append(question)
        Question.objects.bulk_create(questions, batch_size=1000)
        questions = list(Question.objects.all())
        for question in tqdm(questions):
            question_tags = random.sample(tags, min(5, len(tags)))
            question.tags.set(question_tags)

        answers = []
        for _ in tqdm(range(num_answers)):
            content = fake.text(max_nb_chars=500)
            author = random.choice(users)
            question = random.choice(questions)
            answer = Answer(content=content, author=author, question=question)
            if random.random() < 0.1:
                answer.is_accepted = True
            answers.append(answer)
        Answer.objects.bulk_create(answers, batch_size=1000)
        answers = list(Answer.objects.all())

        question_likes = []
        question_like_users = set()
        for _ in tqdm(range(num_question_likes)):
            user = random.choice(users)
            question = random.choice(questions)
            while (user.id, question.id) in question_like_users:
                user = random.choice(users)
                question = random.choice(questions)
            question_like_users.add((user.id, question.id))
            like_type = random.choice(['like', 'dislike'])
            question_like = QuestionLike(user=user, question=question, type=like_type)
            question_likes.append(question_like)
        QuestionLike.objects.bulk_create(question_likes, batch_size=1000)
        for question in tqdm(questions):
            likes = QuestionLike.objects.filter(question=question, type='like').count()
            dislikes = QuestionLike.objects.filter(question=question, type='dislike').count()
            question.rating = likes - dislikes
            question.save()

        answer_likes = []
        answer_like_users = set()
        for _ in tqdm(range(num_answer_likes)):
            user = random.choice(users)
            answer = random.choice(answers)
            while (user.id, answer.id) in answer_like_users:
                user = random.choice(users)
                answer = random.choice(answers)
            answer_like_users.add((user.id, answer.id))
            like_type = random.choice(['like', 'dislike'])
            answer_like = AnswerLike(user=user, answer=answer, type=like_type)
            answer_likes.append(answer_like)
        AnswerLike.objects.bulk_create(answer_likes, batch_size=1000)
        for answer in tqdm(answers):
            likes = AnswerLike.objects.filter(answer=answer, type='like').count()
            dislikes = AnswerLike.objects.filter(answer=answer, type='dislike').count()
            answer.rating = likes - dislikes
            answer.save()

        for question in tqdm(questions):
            has_accepted = Answer.objects.filter(question=question, is_accepted=True).exists()
            question.is_answered = has_accepted
            question.save()