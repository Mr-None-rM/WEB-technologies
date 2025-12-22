from django import forms
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Question, Tag, Answer

User = get_user_model()

class AskQuestionForm(forms.Form):
    title = forms.CharField(label="Title", max_length=200, required=True, widget=forms.TextInput(attrs={'class': 'form_input'}))
    content = forms.CharField(label="Content", max_length=5000, required=True, widget=forms.Textarea(attrs={'class': 'form_textarea', 'rows': 10}))
    tags_input = forms.CharField(label="Tags", max_length=260, required=True, widget=forms.TextInput(attrs={'class': 'form_input'}))
    
    def __init__(self, *args, **kwargs):
        self.author = kwargs.pop('author', None)
        super().__init__(*args, **kwargs)
    
    def clean_tags_input(self):
        tags_input = self.cleaned_data.get('tags_input', '').strip()
        if not tags_input:
            raise forms.ValidationError('At least one tag is required')
        
        tag_names = []
        seen = set()
        for tag in tags_input.split(','):
            tag = tag.strip()
            if tag:
                tag_lower = tag.lower()
                if tag_lower not in seen:
                    seen.add(tag_lower)
                    tag_names.append(tag)
        
        if not tag_names:
            raise forms.ValidationError('Please enter at least one valid tag')
        
        if len(tag_names) > 5:
            raise forms.ValidationError('Maximum 5 tags allowed')
        
        for tag in tag_names:
            if len(tag) > 50:
                raise forms.ValidationError(f'Tag "{tag[:20]}..." is too long (max 50 characters)')
        
        return ', '.join(tag_names)
    
    @transaction.atomic
    def save(self):

        question = Question.objects.create(
            title=self.cleaned_data['title'],
            content=self.cleaned_data['content'],
            author=self.author
        )
        
        tag_names = [tag.strip() for tag in self.cleaned_data['tags_input'].split(',')]
        
        for tag_name in tag_names:
            if tag_name:
                tag_name_lower = tag_name.lower()
                tag, created = Tag.objects.get_or_create(name=tag_name_lower)
                question.tags.add(tag)
        
        return question
    
class AnswerForm(forms.Form):
    content = forms.CharField(label="Content", max_length=5000, required=True, widget=forms.Textarea(attrs={'class': 'form_textarea', 'rows': 10}))
    
    def __init__(self, *args, **kwargs):
        self.author = kwargs.pop('author', None)
        self.question = kwargs.pop('question', None)
        super().__init__(*args, **kwargs)
    
    @transaction.atomic
    def save(self):

        if not self.author or not self.question:
            raise ValueError("Author and question must be provided when saving an answer")
        
        answer = Answer.objects.create(
            content=self.cleaned_data['content'],
            question=self.question,
            author=self.author
        )
        
        return answer