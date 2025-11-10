from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Profile
from django.contrib.auth import authenticate

class UserRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    nickname = serializers.CharField(max_length=50, required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    avatar = serializers.ImageField(required=False, allow_null=True, use_url=False)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('This username is already taken')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('This email is already registered')
        return value

    def validate_nickname(self, value):
        if Profile.objects.filter(nickname=value).exists():
            raise serializers.ValidationError('This nickname is already taken')
        return value

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match'
            })
        return data

    def create(self, validated_data):
        avatar = validated_data.get('avatar')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        Profile.objects.create(
            user=user,
            nickname=validated_data['nickname'],
            avatar = avatar
        )
        return user
    
class UserSettingsSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(source='profile.nickname', max_length=50)
    avatar = serializers.ImageField(source='profile.avatar', required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'nickname', 'avatar']

    def validate_username(self, value):
        if User.objects.filter(username=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('This email is already registered.')
        return value

    def validate_nickname(self, value):
        if Profile.objects.filter(nickname=value).exclude(user=self.instance).exists():
            raise serializers.ValidationError('This nickname is already taken.')
        return value

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        profile = instance.profile
        profile.nickname = profile_data.get('nickname', profile.nickname)
        if 'avatar' in profile_data:
            profile.avatar = profile_data['avatar']
        profile.save()
        return instance

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        if username and password:
            if not User.objects.filter(username=username).exists():
                raise serializers.ValidationError({
                    'username': 'User with this username does not exist'
                })
            user = authenticate(username=username, password=password)
            if user is None:
                raise serializers.ValidationError({
                    'password': 'Invalid password'
                })
            if not user.is_active:
                raise serializers.ValidationError({
                    'username': 'This account is inactive'
                })
            data['user'] = user
        return data