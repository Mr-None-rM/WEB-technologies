from django.contrib import admin
from .models import Question, Answer, Tag, AnswerLike, QuestionLike

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'rating', 'is_answered', 'created_at']
    list_filter = ['is_answered', 'created_at', 'tags']
    search_fields = ['title', 'content']
    filter_horizontal = ['tags']

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['content_preview', 'question', 'author', 'rating', 'is_accepted', 'created_at']
    list_filter = ['is_accepted', 'created_at']
    search_fields = ['content', 'question__title']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Ответ'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'questions_count', 'created_at']
    search_fields = ['name']
    
    def questions_count(self, obj):
        return obj.questions.count()
    questions_count.short_description = 'Количество вопросов'

@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ['question', 'user', 'type', 'created_at']
    list_filter = ['type', 'created_at']

@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ['answer', 'user', 'type', 'created_at']
    list_filter = ['type', 'created_at']