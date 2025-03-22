from django.contrib import admin
from .models import Post, Media

class MediaInline(admin.TabularInline):
    model = Media
    extra = 1

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('creator', 'text_preview', 'is_paid', 'price', 'created_at')
    list_filter = ('is_paid', 'creator')
    search_fields = ('text', 'creator__username')
    inlines = [MediaInline]
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text'

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('post', 'media_type', 'created_at')
    list_filter = ('media_type', 'post__creator')
