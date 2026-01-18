from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('hot/', views.HotQuestions.as_view(), name='hot'),
    path('search/', views.Search.as_view(), name='search'),
    path('question/<int:question_id>/', views.QuestionDetail.as_view(), name='question_detail'),
    path('ask/', views.AskQuestion.as_view(), name='ask'),
    path('tag/<int:tag_id>/', views.TagQuestions.as_view(), name='tag_questions'),
    path('question/<int:question_id>/vote/', views.vote_question, name='vote_question'),
    path('question/<int:question_id>/answer/', views.CreateAnswerView.as_view(), name='answer_create'),
    path('answer/<int:answer_id>/vote/', views.vote_answer, name='vote_answer'),
    path('answer/<int:answer_id>/toggle_accept/', views.toggle_accept_answer, name='toggle_accept_answer'),
    path('search/popup/', views.SearchPopupView.as_view(), name='search_popup'),
]
