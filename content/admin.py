from django.contrib import admin
from .models import Post, Media

class MediaInline(admin.TabularInline):
    model = Media
    extra = 1

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'visibility', 'price', 'created_at')
    list_filter = ('visibility', 'created_at')
    search_fields = ('title', 'text', 'creator__username')
    inlines = [MediaInline]
    date_hierarchy = 'created_at'

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('post', 'media_type', 'created_at')
    list_filter = ('media_type', 'created_at')
    search_fields = ('post__title', 'post__creator__username')
