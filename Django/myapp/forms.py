from django import forms
from .models import Question, Tag

class AskQuestionForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form_input',
            'placeholder': 'Enter your question title'
        }),
        error_messages={
            'required': 'Title is required',
            'max_length': 'Title cannot be longer than 200 characters'
        }
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form_textarea', 
            'placeholder': 'Describe your question in detail',
            'rows': 6
        }),
        error_messages={
            'required': 'Content is required'
        }
    )
    tags_input = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form_input',
            'placeholder': 'Enter tags separated by commas (e.g., python, django, web)'
        }),
        error_messages={
            'required': 'At least one tag is required'
        }
    )
    
    def clean_tags_input(self):
        tags_input = self.cleaned_data['tags_input'].strip()
        if not tags_input:
            raise forms.ValidationError('At least one tag is required')
        tag_names = [tag.strip() for tag in tags_input.split(',')]
        valid_tags = [tag for tag in tag_names if tag]
        if not valid_tags:
            raise forms.ValidationError('Please enter at least one valid tag')
        if len(valid_tags) > 5:
            raise forms.ValidationError('Maximum 5 tags allowed')
        return tags_input

    def save(self, user):
        title = self.cleaned_data['title']
        content = self.cleaned_data['content']
        tags_input = self.cleaned_data['tags_input']
        question = Question.objects.create(
            title=title,
            content=content,
            author=user
        )
        tag_names = [tag.strip() for tag in tags_input.split(',')]
        for tag_name in tag_names:
            if tag_name:
                tag_name_lower = tag_name.lower()
                tag, created = Tag.objects.get_or_create(name=tag_name_lower)
                question.tags.add(tag)
        return question