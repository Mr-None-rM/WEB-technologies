from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['nickname', 'user', 'created_at']
    search_fields = ['nickname', 'user__username']
    list_filter = ['created_at']
