from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import FileExtensionValidator
from .models import Profile

class UserRegistrationForm(forms.Form):
    username = forms.CharField(label="Username", max_length=150, required=True)
    email = forms.EmailField(label="Email", widget=forms.EmailInput, required=True)
    nickname = forms.CharField(label="Nickname", max_length=50, required=True)
    password = forms.CharField(label="Password", max_length=150, widget=forms.PasswordInput, required=True, validators=[validate_password])
    password_confirm = forms.CharField(label="Confirm Password", max_length=150, widget=forms.PasswordInput, required=True)
    avatar = forms.ImageField(
        widget=forms.FileInput, 
        required=False,
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
            message='Unsupported file format. Allowed formats: JPG, JPEG, PNG, GIF, BMP, WEBP'
        )]
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered')
        return email.lower()
    
    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        if Profile.objects.filter(nickname=nickname).exists():
            raise forms.ValidationError('This nickname is already taken')
        return nickname
    
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if not avatar:
            return avatar
        max_file_size = 5 * 1024 * 1024
        if avatar.size > max_file_size:
            raise forms.ValidationError('File size is too large. Maximum allowed size is 5MB')
        min_file_size = 1
        if avatar.size < min_file_size:
            raise forms.ValidationError('File appears to be empty')
        return avatar
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Passwords do not match')
        return cleaned_data
    
    def save(self):
        with transaction.atomic():
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password']
            )
            
            Profile.objects.create(
                user=user,
                nickname=self.cleaned_data['nickname'],
                avatar=self.cleaned_data.get('avatar')
            )
        return user
    
class UserSettingsForm(forms.ModelForm):
    avatar = forms.ImageField(
        label="", 
        widget=forms.FileInput, 
        required=False,
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
            message='Unsupported file format. Allowed formats: JPG, JPEG, PNG, GIF, BMP, WEBP'
        )]
    )
    username = forms.CharField(label="Username", max_length=150, required=True)
    email = forms.EmailField(label="Email", widget=forms.EmailInput, required=True)
    nickname = forms.CharField(label="Nickname", max_length=50, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        profile = self.instance.profile
        self.fields['nickname'].initial = profile.nickname
        self.fields['avatar'].initial = profile.avatar
    
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if not avatar:
            return avatar
        max_file_size = 5 * 1024 * 1024
        if avatar.size > max_file_size:
            raise forms.ValidationError('File size is too large. Maximum allowed size is 5MB')
        min_file_size = 1
        if avatar.size < min_file_size:
            raise forms.ValidationError('File appears to be empty')
        return avatar
    
    def clean_username(self):
        username = self.cleaned_data.get('username').strip()
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This username is already taken.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email').strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email is already registered.')
        return email
    
    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname').strip()
        if Profile.objects.filter(nickname__iexact=nickname).exclude(user=self.instance).exists():
            raise forms.ValidationError('This nickname is already taken.')
        return nickname
    
    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        nickname = self.cleaned_data['nickname']
        avatar = self.cleaned_data.get('avatar')
        if commit:
            user.save()
            try:
                profile = user.profile
            except ObjectDoesNotExist:
                profile = Profile.objects.create(
                    user=user,
                    nickname=nickname
                )
            profile.nickname = nickname
            if avatar is not None:
                profile.avatar = avatar
            profile.save()
        return user

class LoginForm(forms.Form):
    username = forms.CharField(label="Username", max_length=150, required=True)
    password = forms.CharField(label="Password", max_length=150, widget=forms.PasswordInput, required=True)
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError("Invalid username or password. Please try again.")
            cleaned_data['user'] = user
        return cleaned_data