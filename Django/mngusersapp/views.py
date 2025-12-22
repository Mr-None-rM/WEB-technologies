from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView, UpdateView
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.db import transaction
from .forms import UserRegistrationForm, UserSettingsForm, LoginForm

class LoginView(FormView):
    template_name = 'registration/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('index')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        user = form.cleaned_data['user']
        login(self.request, user)
        return super().form_valid(form)

class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('index')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)
    
    @transaction.atomic
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

class Settings(LoginRequiredMixin, UpdateView):
    template_name = 'registration/settings.html'
    form_class = UserSettingsForm
    success_url = reverse_lazy('index')
    
    def get_object(self, queryset=None):
        return self.request.user