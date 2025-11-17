from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import Profile

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)
        parser.add_argument('--email', required=True)
        parser.add_argument('--password', required=True)

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        user = User.objects.create_superuser(username, email, password)
        Profile.objects.get_or_create(
            user=user,
            defaults={'nickname': username}
        )