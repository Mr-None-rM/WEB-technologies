from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('settings/', views.Settings.as_view(), name='settings'),
    path("logout/", LogoutView.as_view(next_page='index'), name="logout"),
]
