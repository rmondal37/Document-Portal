from django.contrib import admin
from .models import User, Post


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'file_field', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['title', 'desc', 'user__username']
    readonly_fields = ['file_date', 'created_at']
